import asyncio
from socket import gaierror
from typing_extensions import Callable

from nonebot import get_driver, get_bot, require
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from nonebot.adapters.satori import Message, MessageSegment
from mcstatus import JavaServer

from .config import Config

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import (  # pylint: disable=C0411,C0413,E0402  # noqa: E402
    scheduler,
)

__plugin_meta__ = PluginMetadata(
    name="xas_checkmc",
    description="",
    usage="",
    config=Config,
)

global_config = get_driver().config
config = Config.parse_obj(global_config)

groups = config.xas_checkmc_groups
server_data = config.xas_checkmc_servers
status_data: dict[str, bool] = {server_name: True for server_name in server_data}


async def check_server(server_name: str, add_msg: Callable[[MessageSegment], None]):
    server_addr = server_data[server_name]
    warning_message_seg = MessageSegment.text(f"警告:服务器 {server_name} 无法连接.\n")
    restoration_message_seg = MessageSegment.text(f"服务器 {server_name} 已恢复.\n")
    try:
        server = await JavaServer.async_lookup(server_addr)
        await server.async_status()
    except TimeoutError:
        if status_data[server_name]:
            add_msg(warning_message_seg)
        status_data[server_name] = False
    except gaierror:
        logger.warning(f"无法解析地址: {server_addr}")
    except OSError as e:
        if (
            str(e) == "Socket did not respond with any information!"
            and status_data[server_name]
        ):
            logger.trace("Socket did not respond with any information!")
            add_msg(warning_message_seg)
        status_data[server_name] = False
    else:
        if not status_data[server_name]:
            add_msg(restoration_message_seg)
        status_data[server_name] = True
    finally:
        logger.trace(f"检测完成: {status_data}")


async def send_msg(message: Message):
    for group in groups:
        await get_bot().call_api("send_message", channel=group, message=message)


@scheduler.scheduled_job("cron", second="0,30")
async def check():
    message = Message()

    def add_msg(message_seg: MessageSegment):
        message.append(message_seg)

    tasks = [
        asyncio.create_task(check_server(server_name, add_msg))
        for server_name in server_data
    ]
    await asyncio.wait(tasks)
    if not message:
        return
    await send_msg(message)
