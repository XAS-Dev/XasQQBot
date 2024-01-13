from nonebot import get_driver
from typing import TypedDict

from mcstatus import JavaServer, BedrockServer

from .config import Config, ServerType

global_config = get_driver().config
config = Config.parse_obj(global_config)


class Player(TypedDict):
    max: int
    online: int


class McStatus(TypedDict):
    player: Player


match config.mc_type:
    case ServerType.JAVA:
        server = JavaServer(config.mc_host, config.mc_port)
    case ServerType.BEDROCK:
        server = BedrockServer(config.mc_host, config.mc_port)


async def getStatus() -> McStatus:
    status = server.status()
    result = McStatus(
        {
            "player": {
                "online": status.players.online,
                "max": status.players.max,
            },
        }
    )
    match config.mc_type:  # type: ignore
        case ServerType.JAVA:
            result["player"]["sample"] = [i.name for i in status.players.sample or []]  # type: ignore
        case ServerType.BEDROCK:
            ...
    return result
