from mcstatus import JavaServer
from mcstatus.status_response import JavaStatusResponse
from nonebot import get_plugin_config, logger, require
from nonebot.plugin import PluginMetadata
from typing_extensions import Optional

from .config import Config

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import (  # pylint: disable=C0411,C0413,E0402  # noqa: E402
    scheduler,
)

require("xas_chatgpt")
from ..xas_chatgpt.api import (  # pylint: disable=C0411,C0413,E0402  # noqa: E402
    ChatAskEvent,
    on_chat_ask,
)

__plugin_meta__ = PluginMetadata(
    name="xas_chat_mcstatus",
    description="",
    usage="",
    config=Config,
)


config = get_plugin_config(Config)
server_host = config.xas_gpt_mcstatus_server_host
server_port = config.xas_gpt_mcstatus_server_port


status: Optional[JavaStatusResponse] = None


async def chat_ask_listener(event: ChatAskEvent):
    prefix = ""
    if status is None:
        prefix = "目前无法获取服务器状态.\n"
    else:
        prefix = f"服务器目前有 {status.players.online}/{status.players.max} 名玩家在线.\n"
    if status and status.players.sample:
        prefix += f"分别为 {','.join([i.name for i in status.players.sample])}\n"
    event.message = prefix + event.message


on_chat_ask(chat_ask_listener)


@scheduler.scheduled_job(trigger="cron", second="0,15,30,45")
async def update_status():
    global status  # pylint: disable=W0603
    server = JavaServer(server_host, server_port, 10)
    try:
        status = await server.async_status()
    except Exception as e:  # noqa: E722 pylint: disable=W0702, W0718
        logger.trace("无法更新服务器状态.")
        logger.error(e)
        status = None
