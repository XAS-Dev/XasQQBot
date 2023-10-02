import random

from nonebot import get_driver, on_message
from nonebot.adapters.red.event import GroupMessageEvent

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)

repeaterDict = {}

message = on_message()


@message.handle()
async def _(event: GroupMessageEvent):
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

    # if (
    #     random.random()
    #     < (repeaterDict[event.peerUin]["count"] ** 2) / config.repetitive_limit**2
    # ) and not repeaterDict[event.peerUin]["is_repeated"]:
    #     # 复读的概率随指数级增长
    if (
        random.random() < repeaterDict[event.peerUin]["count"] / config.repetitive_limit
        and not repeaterDict[event.peerUin]["is_repeated"]
    ):
        repeaterDict[event.peerUin]["is_repeated"] = True
        await message.send(event.get_plaintext())