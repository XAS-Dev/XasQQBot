import random

from nonebot import get_driver, on_message
from nonebot.adapters.red.bot import Bot
from nonebot.adapters.red.event import GroupMessageEvent

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)

repeaterDict = {}

message = on_message(block=False)


@message.handle()
async def _(event: GroupMessageEvent):
    # 忽略指令
    if (
        len(event.get_plaintext()) >= 1
        and event.get_plaintext() in global_config.command_start
    ):
        return
    # 忽略@
    if event.to_me:
        return

    if event.peerUin not in repeaterDict:
        repeaterDict[event.peerUin] = {
            "message": event.get_plaintext(),
            "count": 1,
            "is_repeated": False,
        }
    elif repeaterDict[event.peerUid]["message"] == event.get_plaintext():  # noqa: E501
        repeaterDict[event.peerUin]["count"] += 1
    else:
        repeaterDict[event.peerUin] = {
            "message": event.get_plaintext(),
            "count": 1,
            "is_repeated": False,
        }

    if config.probability_index_growth:  # type: ignore
        if (
            random.random()
            < (repeaterDict[event.peerUin]["count"] ** 2) / config.repetitive_limit**2  # type: ignore  # noqa: E501
        ) and not repeaterDict[event.peerUin]["is_repeated"]:
            # 复读的概率随指数级增长
            repeaterDict[event.peerUin]["is_repeated"] = True
            await message.send(event.get_plaintext())
    else:
        if (
            random.random() < repeaterDict[event.peerUin]["count"] / config.repetitive_limit  # type: ignore  # noqa: E501
            and not repeaterDict[event.peerUin]["is_repeated"]
        ):
            # 复读的概率线性增长
            repeaterDict[event.peerUin]["is_repeated"] = True
            await message.send(event.get_plaintext())
