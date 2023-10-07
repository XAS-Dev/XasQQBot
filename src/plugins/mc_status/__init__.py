from nonebot import get_driver
from mcstatus import JavaServer, BedrockServer

from .config import Config, ServerType

global_config = get_driver().config
config = Config.parse_obj(global_config)

match config.mc_type:
    case ServerType.JAVA:
        server = JavaServer(config.mc_host, config.mc_port)
    case ServerType.BEDROCK:
        server = BedrockServer(config.mc_host, config.mc_port)


async def getStatus():
    status = server.status()
    result = {
        "player": {
            "online": status.players.online,
            "max": status.players.max,
        },
    }
    match config.mc_type:  # type: ignore
        case ServerType.JAVA:
            result["player"]["sample"] = [i.name for i in status.players.sample or []]  # type: ignore
        case ServerType.BEDROCK:
            ...
    return result
