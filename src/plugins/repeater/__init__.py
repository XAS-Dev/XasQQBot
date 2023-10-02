import random
import hashlib

from nonebot import get_driver, on_message
from nonebot.exception import FinishedException
from nonebot.adapters.red.event import GroupMessageEvent
from nonebot.adapters.red.message import Message

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)

repeaterDict = {}

message = on_message(block=False)


def getMessageHash(message: Message):
    resultList = []
    for i in message:
        match i.type:
            case "text":
                resultList.append(
                    hashlib.sha256(("TEXT:" + str(i)).encode()).hexdigest()
                )
            case "image":
                resultList.append(
                    hashlib.sha256(
                        ("IMAGE:" + i.data.get("md5", "")).encode()
                    ).hexdigest()
                )
            case _:
                raise FinishedException
    # print(hashlib.sha256(" ".join(resultList).encode()).hexdigest())
    return hashlib.sha256(" ".join(resultList).encode()).hexdigest()


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
            "message_hash": getMessageHash(event.get_message()),
            "count": 1,
            "is_repeated": False,
        }
    elif repeaterDict[event.peerUid]["message_hash"] == getMessageHash(
        event.get_message()
    ):  # noqa: E501
        repeaterDict[event.peerUin]["count"] += 1
    else:
        repeaterDict[event.peerUin] = {
            "message_hash": getMessageHash(event.get_message()),
            "count": 1,
            "is_repeated": False,
        }

    if config.probability_index_growth:  # type: ignore
        if (
            random.random()
            < ((repeaterDict[event.peerUin]["count"] - config.repetitive_minimum) ** 2)  # type: ignore  # noqa: E501
            / (config.repetitive_limit - config.repetitive_minimum) ** 2  # type: ignore
        ) and not repeaterDict[event.peerUin]["is_repeated"]:
            # 复读的概率随指数级增长
            repeaterDict[event.peerUin]["is_repeated"] = True
            await message.send(event.get_message())
    else:
        if (
            random.random()
            < (repeaterDict[event.peerUin]["count"] - config.repetitive_minimum)  # type: ignore  # noqa: E501
            / (config.repetitive_limit - config.repetitive_minimum)  # type: ignore
            and not repeaterDict[event.peerUin]["is_repeated"]
        ):
            # 复读的概率线性增长
            repeaterDict[event.peerUin]["is_repeated"] = True
            await message.send(event.get_message())
