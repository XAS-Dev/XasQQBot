import json
from typing import Dict, List, Callable
from datetime import datetime, timedelta
from asyncio import Lock

from nonebot import get_driver
from nonebot.log import logger
from nonebot.rule import Rule
from nonebot.plugin import PluginMetadata, require
from nonebot.plugin import on_message, on_command
from nonebot.params import EventPlainText, CommandArg
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.adapters.satori.event import MessageCreatedEvent
from nonebot.adapters.satori.message import Message
from openai import APIConnectionError
from openai.types.chat import ChatCompletionMessageParam
from typing_extensions import TypedDict


from .config import Config
from .chatgpt import ChatGPT

require("xas_util")
from ..xas_util import (  # pylint: disable=C0411,C0413,E0402  # noqa: E402
    create_quote_or_at_message,
    rule_check_trust,
    rule_check_tome,
)

require("nonebot_plugin_localstore")
from nonebot_plugin_localstore import (  # pylint: disable=C0411,C0413   # noqa: E402
    get_data_dir,
)


class Context(TypedDict):
    messages: List[ChatCompletionMessageParam]
    model: str
    last_time: datetime
    extend_data: Dict[str, str]


__plugin_meta__ = PluginMetadata(
    name="xas_chatgpt",
    description="",
    usage="",
    config=Config,
)

SessionId = str

global_config = get_driver().config
config = Config.parse_obj(global_config)
extend_list = []
data_dir = get_data_dir(__plugin_meta__.name)
system_prompt_file_dir = data_dir / "system_prompt.json"
default_prompt = config.xas_chatgpt_default_prompt
system_prompt_config: Dict[SessionId, str] = {}
context_dict: Dict[SessionId, Context] = {}
lock_dict: Dict[SessionId, Lock] = {}


def save_system_prompt():
    with open(
        system_prompt_file_dir,
        "w",
        encoding="utf-8",
    ) as fw:
        json.dump(system_prompt_config, fw)  # type: ignore


def set_default_context(channel_id: str):
    context_dict[channel_id] = {
        "messages": [],
        "model": config.xas_chatgpt_default_model,
        "last_time": datetime.now(),
        "extend_data": {},
    }


if system_prompt_file_dir.exists():
    with open(system_prompt_file_dir, encoding="utf-8") as fr:
        system_prompt_config = json.load(fr)
else:
    save_system_prompt()


def register_extend(extend: Callable[[dict], dict]):
    extend_list.append(extend)


async def rule_check_enable(event: MessageCreatedEvent):
    result = bool(
        event.channel and (event.channel.id in config.xas_chatgpt_enable_channel)
    )
    logger.trace(f"rule enable: {result}")
    return result


async def rule_check_not_command(message=EventPlainText()):
    result = not any([message.startswith(i) for i in global_config.command_start])
    logger.trace(f"rule not_command: {result}")
    return result


Chat = on_message(
    priority=10,
    rule=Rule(rule_check_tome) & Rule(rule_check_not_command) & Rule(rule_check_enable),
)


@Chat.handle()
async def chat(
    matcher: Matcher,
    event: MessageCreatedEvent,
    message_text=EventPlainText(),
):
    logger.success("触发ChatGPT")
    if event.get_session_id() not in lock_dict:
        lock_dict[event.get_session_id()] = Lock()
    logger.trace(f"{event.get_session_id()} 已加锁.")
    await lock_dict[event.get_session_id()].acquire()

    channel_id: str = event.channel and event.channel.id  # type: ignore
    if (
        channel_id not in context_dict
        or context_dict[channel_id]["last_time"]
        + timedelta(seconds=config.xas_chatgpt_context_validity_period)
        < datetime.now()
    ):
        set_default_context(channel_id)
        logger.trace("超时或不存在上下文, 上下文已设置为默认值.")
    context_dict[channel_id]["last_time"] = datetime.now()
    messages = context_dict[channel_id]["messages"]
    extend_data = context_dict[channel_id]["extend_data"]
    extend_data = {**extend_data, "now_tine": str(datetime.now())}

    for extend in extend_list:
        extend_data.update(extend(extend_data))
    system_prompt = system_prompt_config.get(channel_id) or default_prompt
    system_prompt = system_prompt.format_map(extend_data)
    try:
        print(event)
        answer, new_messages = await ChatGPT.chat(
            f"{(event.member and event.member.name) or (event.member and event.member.nick)}"
            f"({event.get_user_id()}): {message_text}",
            messages,
            system_prompt,
        )
    except APIConnectionError:
        logger.error(create_quote_or_at_message(event) + "错误: API连接错误.")
        await matcher.finish(create_quote_or_at_message(event) + "错误: API连接错误.")
    finally:
        lock_dict[event.get_session_id()].release()
        logger.trace(f"{event.get_session_id()} 已解锁.")
    context_dict[channel_id]["messages"] = new_messages
    logger.trace(new_messages)
    logger.success(create_quote_or_at_message(event) + answer)
    await matcher.finish(create_quote_or_at_message(event) + answer)


SwitchGPT3 = on_command(
    "切换GPT3.5",
    aliases={"变baka"},
    rule=Rule(rule_check_trust) & Rule(rule_check_enable),
)


@SwitchGPT3.handle()
async def switch_gpt3(matcher: Matcher, event: MessageCreatedEvent):
    channel_id: str = event.channel and event.channel.id  # type: ignore
    if channel_id not in context_dict:
        set_default_context(channel_id)
    context_dict[channel_id]["model"] = "gpt-3.5-turbo"
    await matcher.finish(create_quote_or_at_message(event) + "已切换到 ChatGPT3.5.")


SwitchGPT4 = on_command(
    "切换GPT4",
    aliases={"变聪明", "IQBoost"},
    rule=Rule(rule_check_trust) & Rule(rule_check_enable),
)


@SwitchGPT4.handle()
async def switch_gpt4(matcher: Matcher, event: MessageCreatedEvent):
    channel_id: str = event.channel and event.channel.id  # type: ignore
    if channel_id not in context_dict:
        set_default_context(channel_id)
    context_dict[channel_id]["model"] = "gpt-4"
    await matcher.finish(create_quote_or_at_message(event) + "已切换到 GPT4.")


ViewModel = on_command(
    "查看模型",
    aliases={"智商", "IQ"},
    rule=Rule(rule_check_trust) & Rule(rule_check_enable),
)


@ViewModel.handle()
async def view_model(matcher: Matcher, event: MessageCreatedEvent):
    channel_id: str = event.channel and event.channel.id  # type: ignore
    if channel_id not in context_dict:
        set_default_context(channel_id)
    await matcher.finish(f"当前模型: {context_dict[channel_id]['model']}")


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
    logger.trace(f"提示词: {arg_text}")
    if channel_id not in system_prompt_config:
        set_default_context(channel_id)
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
        await matcher.finish(
            create_quote_or_at_message(event) + system_prompt_config[channel_id]
        )
    await matcher.finish(create_quote_or_at_message(event) + "[默认]" + default_prompt)


CleanMessages = on_command(
    "清除对话", aliases={"失忆"}, rule=Rule(rule_check_trust) & Rule(rule_check_enable)
)


@CleanMessages.handle()
async def clean_message(matcher: Matcher, event: MessageCreatedEvent):
    channel_id: str = event.channel and event.channel.id  # type: ignore
    if channel_id in context_dict:
        quantity = len(context_dict[channel_id]["messages"])
        context_dict[channel_id]["messages"] = []
        await matcher.finish(
            create_quote_or_at_message(event) + f"已清除 {quantity} 条对话记录."
        )
    await matcher.finish(create_quote_or_at_message(event) + "没有对话记录")
