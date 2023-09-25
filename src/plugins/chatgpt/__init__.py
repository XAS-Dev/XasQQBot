from urllib.parse import urljoin

from nonebot import get_driver
from nonebot.log import logger
from nonebot.rule import to_me
from nonebot.params import EventPlainText, Depends
from nonebot.plugin.on import on_message, on_command
from nonebot.internal.matcher.matcher import Matcher
from nonebot.adapters.red.message import Message, MessageSegment
from nonebot.adapters.red.event import PrivateMessageEvent, GroupMessageEvent
import httpx

from .config import Config
from .chatGpt import chatGpt

global_config = get_driver().config
config = Config.parse_obj(global_config)


# 获取检查器
def getChecker(matcher: Matcher):
    async def checkUser(
        event: PrivateMessageEvent | GroupMessageEvent,
    ) -> PrivateMessageEvent | GroupMessageEvent:
        match event.get_event_name():
            case "message.group":
                if str(event.peerUin) not in config.chatgpt_enable_group:
                    logger.debug("不允许的群聊")
                    await matcher.finish()
                return event
            case "message.private":
                if str(event.senderUin) not in config.chatgpt_enable_user:
                    logger.debug("不允许的用户")
                    await matcher.finish("权限不足")
        return event

    return checkUser
    # return lambda event: event


# 获取标识id
def getIdentifying(event: PrivateMessageEvent | GroupMessageEvent):
    match event.__class__.__name__:
        case "GroupMessageEvent":
            return f"group.{event.peerUin}"
        case "PrivateMessageEvent":
            return f"private.{event.senderUin}"
        case _:
            logger.warning("获取标识id失败")


# 获取余额
checkBalance = on_command("余额", block=True)


@checkBalance.handle()
async def _(
    event: PrivateMessageEvent
    | GroupMessageEvent = Depends(getChecker(checkBalance)),  # type:ignore
):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            urljoin(config.chatgpt_api, "../dashboard/billing/credit_grants"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.chatgpt_key}",
            },
        )
    message = Message(
        [
            *(
                (
                    MessageSegment.reply(event.msgSeq, event.msgId, event.senderUin),
                    MessageSegment.at(event.get_user_id(), event.sendMemberName),
                    MessageSegment.text(" "),
                )
                if event.get_event_name() == "message.group"
                else ()
            ),
            MessageSegment.text(
                f"ChatGPT剩余余额: {response.json()['total_available']} CNY"
            ),
        ]
    )
    await checkBalance.finish(message)


# 清除历史
cleanHistory = on_command("清除历史", aliases={"失忆"}, priority=2, block=True)


@cleanHistory.handle()
async def _(
    event: PrivateMessageEvent
    | GroupMessageEvent = Depends(getChecker(checkBalance)),  # type:ignore
):
    conversation = chatGpt.conversationRecord.get(getIdentifying(event))  # type: ignore
    length = len(conversation or [])
    if conversation:
        chatGpt.conversationRecord.get(getIdentifying(event))["conversation"] = []  # type: ignore  # noqa: E501
        chatGpt.save()
    message = Message(
        [
            *(
                (
                    MessageSegment.reply(event.msgSeq, event.msgId, event.senderUin),
                    MessageSegment.at(event.get_user_id(), event.sendMemberName),
                    MessageSegment.text(" "),
                )
                if event.get_event_name() == "message.group"
                else ()
            ),
            MessageSegment.text(f"已清除{length}条历史记录"),
        ]
    )
    await checkBalance.finish(message)


# 获取完整历史记录
getHistory = on_command("完整历史记录", priority=1, block=True)


@getHistory.handle()
async def _(
    event: PrivateMessageEvent
    | GroupMessageEvent = Depends(getChecker(getHistory)),  # type:ignore
):
    translateDict = {"user": "用户", "assistant": "XAS bot"}
    count = 0  # 总长
    result = Message()
    result.append("历史记录:\n")
    for i in chatGpt.conversationRecord[getIdentifying(event)]:  # type:ignore
        result.append(
            MessageSegment.text(f"{translateDict[i['role']]}: {i['content']}")
        ).append("\n")
        count += len(i["content"])  # 统计字数
    result.append("\n")
    result.append(f"共 {count} 字")
    await getHistory.finish(result)


# 聊天
chat = on_message(rule=to_me(), priority=2)


@chat.handle()
async def _(
    event: PrivateMessageEvent
    | GroupMessageEvent = Depends(getChecker(chat)),  # type:ignore
    message: str = EventPlainText(),
):
    if len(message) >= 1 and message[0] in global_config.command_start:
        return
    logger.info("开始向ChatGPT提问")
    answer, error = await chatGpt.chat(getIdentifying(event), message)  # type:ignore
    logger.info("提问完成")
    if not answer:
        await chat.finish(f"错误: {error.__class__.__name__}: {str(error)}")
    resultMessage = Message(
        [
            *(
                (
                    MessageSegment.reply(event.msgSeq, event.msgId, event.senderUin),
                    MessageSegment.at(event.get_user_id(), event.sendMemberName),
                    MessageSegment.text(" "),
                )
                if event.get_event_name() == "message.group"
                else ()
            ),
            MessageSegment.text(answer),
        ]
    )
    await chat.finish(resultMessage)
