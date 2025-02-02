import json
import re
from asyncio import Lock
from datetime import datetime, timedelta
from typing import Dict, List

from nonebot import get_driver, get_plugin_config
from nonebot.adapters.satori.event import MessageCreatedEvent
from nonebot.adapters.satori.message import Message
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, EventPlainText
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata, on_command, on_message, require
from nonebot.rule import Rule
from openai import APIConnectionError, InternalServerError
from openai.types.chat import ChatCompletionMessageParam
from typing_extensions import TypedDict

from .api import ChatAnswerEvent, ChatAskEvent, ChatInitEvent, chat_answer_listener, chat_ask_listener, chat_init_listener
from .chatgpt import ChatGPT
from .config import Config

require("xas_util")
from ..xas_util import (  # pylint: disable=C0411,C0413,E0402  # noqa: E402
    create_quote_or_at_message,
    rule_check_tome,
    rule_check_trust,
)

require("nonebot_plugin_localstore")
from nonebot_plugin_localstore import (  # pylint: disable=C0411,C0413,E0402  # noqa: E402
    get_data_dir,
)

__plugin_meta__ = PluginMetadata(
    name="xas_chatgpt",
    description="",
    usage="",
    config=Config,
)


class Context(TypedDict):
    system_prompt: str
    messages: List[ChatCompletionMessageParam]
    model: str
    last_time: datetime


__plugin_meta__ = PluginMetadata(
    name="xas_chatgpt",
    description="",
    usage="",
    config=Config,
)

type SessionId = str

global_config = get_driver().config
config = get_plugin_config(Config)
data_dir = get_data_dir(__plugin_meta__.name)
system_prompt_file_dir = data_dir / "system_prompt.json"
system_prompt_config: Dict[SessionId, str] = {}
context_dict: Dict[SessionId, Context] = {}
lock_dict: Dict[SessionId, Lock] = {}

enable_channel = config.xas_chatgpt_enable_channel
default_model = config.xas_chatgpt_default_model
advanced_model = config.xas_chatgpt_advanced_model
default_prompt = config.xas_chatgpt_default_prompt
context_validity_period = config.xas_chatgpt_context_validity_period


def save_system_prompt():
    with open(
        system_prompt_file_dir,
        "w",
        encoding="utf-8",
    ) as fw:
        json.dump(system_prompt_config, fw, indent=4, ensure_ascii=False)  # type: ignore


async def set_default_context(channel_id: str):
    # emit init event
    system_prompt = system_prompt_config.get(channel_id) or default_prompt
    event_result = await emit_chat_init_event(channel_id, system_prompt)
    context_dict[channel_id] = {
        "system_prompt": event_result.system_prompt,
        "messages": [],
        "model": default_model,
        "last_time": datetime.now(),
    }


# 加载系统提示词配置
if system_prompt_file_dir.exists():
    with open(system_prompt_file_dir, encoding="utf-8") as fr:
        system_prompt_config = json.load(fr)
else:
    save_system_prompt()

# ===== Emitter =====


async def emit_chat_init_event(channel_id: str, system_prompt: str):
    init_event = ChatInitEvent(channel_id, system_prompt)
    for listener in chat_init_listener:
        await listener(init_event)
    return init_event


async def emit_chat_ask_event(channel_id, question: str):
    ask_event = ChatAskEvent(channel_id, message=question)
    for listener in chat_ask_listener:
        await listener(ask_event)
    return ask_event


async def emit_chat_answer_event(channel_id, answer: str):
    answer_event = ChatAnswerEvent(channel_id, message=answer)
    for listener in chat_answer_listener:
        await listener(answer_event)
    return answer_event


# ===== 规则 =====


async def rule_check_enable(event: MessageCreatedEvent):
    is_correct_cannel = bool(event.channel and (event.channel.id in enable_channel))
    match_result = re.match(r"^private:(.+)$", event.channel and event.channel.id)
    is_private = match_result
    is_correct_private = is_private and match_result.group(1) == event.user.id
    result = bool(is_correct_cannel and (not is_private or is_correct_private))
    logger.trace(f"rule check_enable: {result}")
    return result


async def rule_check_not_command(message=EventPlainText()):
    result = not any([message.startswith(i) for i in global_config.command_start])
    logger.trace(f"rule not_command: {result}")
    return result


async def rule_check_is_message(message=EventPlainText()):
    result = bool(message)
    logger.trace(f"rule is_message: {result}")
    return result


# ===== 聊天 =====

Chat = on_message(
    priority=10,
    rule=Rule(rule_check_tome) & Rule(rule_check_not_command) & Rule(rule_check_is_message) & Rule(rule_check_enable),
)


@Chat.handle()
async def chat(
    matcher: Matcher,
    event: MessageCreatedEvent,
    message_text=EventPlainText(),
):
    logger.success("触发ChatGPT")
    channel_id: str = event.channel and event.channel.id  # type: ignore

    lock_dict.setdefault(channel_id, Lock())
    logger.trace(f"{channel_id} 已加锁.")
    await lock_dict[channel_id].acquire()

    if channel_id not in context_dict or context_dict[channel_id]["last_time"] + timedelta(seconds=context_validity_period) < datetime.now():
        await set_default_context(channel_id)
        logger.trace("超时或不存在上下文, 上下文已设置为默认值.")
    context_dict[channel_id]["last_time"] = datetime.now()  # 更新上下文时间

    system_prompt = context_dict[channel_id]["system_prompt"]
    messages = context_dict[channel_id]["messages"]
    model = context_dict[channel_id]["model"]
    name = (event.member and event.member.nick) or (event.user and event.user.nick or event.user.name)
    question = f"{name}({event.get_user_id()}): {message_text}"
    # emit ask event
    event_result = await emit_chat_ask_event(channel_id, question)
    question = event_result.message
    # chat with chatgpt
    try:
        answer, new_messages = await ChatGPT.chat(
            question,
            messages,
            system_prompt,
            model,
        )
    except APIConnectionError as e:
        logger.error(create_quote_or_at_message(event) + "错误: API连接错误." + e.message)
        await matcher.finish(create_quote_or_at_message(event) + "错误: API连接错误.")
    except InternalServerError as e:
        logger.error(create_quote_or_at_message(event) + "错误: 服务器内部错误." + e.message)
        await matcher.finish(create_quote_or_at_message(event) + "错误: 服务器内部错误.")
    finally:
        lock_dict[channel_id].release()
        logger.trace(f"{channel_id} 已解锁.")
    context_dict[channel_id]["messages"] = new_messages
    # emit answer event
    event_result = await emit_chat_answer_event(channel_id, answer)
    answer = event_result.message

    logger.trace(f"最终回复: {answer}")
    logger.success(create_quote_or_at_message(event) + answer)
    await matcher.finish(create_quote_or_at_message(event) + answer)


# ===== 模型切换 =====

SwitchBaseModel = on_command(
    "切换聊天模型",
    aliases={"变baka"},
    rule=Rule(rule_check_trust) & Rule(rule_check_enable),
)


@SwitchBaseModel.handle()
async def switch_gpt3(matcher: Matcher, event: MessageCreatedEvent):
    channel_id: str = event.channel and event.channel.id  # type: ignore
    if channel_id not in context_dict:
        await set_default_context(channel_id)
    context_dict[channel_id]["model"] = default_model
    await matcher.finish(create_quote_or_at_message(event) + f"已切换到 {default_model}")


SwitchAdvancedModel = on_command(
    "切换推理模型",
    aliases={"变聪明", "IQBoost"},
    rule=Rule(rule_check_trust) & Rule(rule_check_enable),
)


@SwitchAdvancedModel.handle()
async def switch_gpt4(matcher: Matcher, event: MessageCreatedEvent):
    channel_id: str = event.channel and event.channel.id  # type: ignore
    if channel_id not in context_dict:
        await set_default_context(channel_id)
    context_dict[channel_id]["model"] = advanced_model
    await matcher.finish(create_quote_or_at_message(event) + f"已切换到 {advanced_model}")


ViewModel = on_command(
    "当前模型",
    aliases={"智商", "IQ"},
    rule=Rule(rule_check_trust) & Rule(rule_check_enable),
)


@ViewModel.handle()
async def view_model(matcher: Matcher, event: MessageCreatedEvent):
    channel_id: str = event.channel and event.channel.id  # type: ignore
    if channel_id not in context_dict:
        await set_default_context(channel_id)
    await matcher.finish(f"当前模型: {context_dict[channel_id]['model']}")


# ===== 提示词设置 =====

SetPrompt = on_command(
    "设置提示词",
    rule=Rule(rule_check_trust) & Rule(rule_check_enable),
    permission=SUPERUSER,
)


@SetPrompt.handle()
async def set_prompt(
    matcher: Matcher,
    event: MessageCreatedEvent,
    arg_text: Message = CommandArg(),
):
    channel_id: str = event.channel and event.channel.id  # type: ignore
    system_prompt_config[channel_id] = arg_text.extract_plain_text()
    save_system_prompt()
    await matcher.finish(create_quote_or_at_message(event) + "设置完成")


GetPrompt = on_command(
    "获取提示词",
    rule=Rule(rule_check_trust) & Rule(rule_check_enable),
    permission=SUPERUSER,
)


@GetPrompt.handle()
async def get_prompt(
    matcher: Matcher,
    event: MessageCreatedEvent,
):
    channel_id: str = event.channel and event.channel.id  # type: ignore
    if channel_id in system_prompt_config:
        await matcher.finish(create_quote_or_at_message(event) + system_prompt_config[channel_id])
    await matcher.finish(create_quote_or_at_message(event) + "[默认]" + default_prompt)


CleanPrompt = on_command(
    "清除提示词",
    rule=Rule(rule_check_trust) & Rule(rule_check_enable),
    permission=SUPERUSER,
)


@CleanPrompt.handle()
async def clean_prompt(
    matcher: Matcher,
    event: MessageCreatedEvent,
):
    channel_id: str = event.channel and event.channel.id  # type: ignore
    if channel_id in system_prompt_config:
        system_prompt_config.pop(channel_id)
    save_system_prompt()
    await matcher.finish(create_quote_or_at_message(event) + "清除完成")


# ===== 对话记录管理 =====

CleanMessages = on_command("清除对话", aliases={"失忆"}, rule=Rule(rule_check_trust) & Rule(rule_check_enable))


@CleanMessages.handle()
async def clean_message(matcher: Matcher, event: MessageCreatedEvent):
    channel_id: str = event.channel and event.channel.id  # type: ignore
    if channel_id in context_dict:
        quantity = len(context_dict[channel_id]["messages"])
        context_dict.pop(channel_id)
        await matcher.finish(create_quote_or_at_message(event) + f"已清除 {quantity} 条对话记录.")
    await matcher.finish(create_quote_or_at_message(event) + "没有对话记录")
