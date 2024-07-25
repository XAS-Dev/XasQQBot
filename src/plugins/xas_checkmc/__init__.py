import asyncio
import dns.resolver
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
status_data: dict[str, int] = {server_name: 0 for server_name in server_data}
fail_count = config.xas_checkmc_fail_count


async def check_server(server_name: str, add_msg: Callable[[MessageSegment], None]):
    server_addr = server_data[server_name]
    warning_message_seg = MessageSegment.text(f"警告:服务器 {server_name} 无法连接.\n")
    restoration_message_seg = MessageSegment.text(f"服务器 {server_name} 已恢复.\n")
    try:
        server = await JavaServer.async_lookup(server_addr)
        await server.async_status()
    except TimeoutError:
        logger.warning(f"连接超时: {server_addr}")
        status_data[server_name] += 1
    except gaierror:
        logger.warning(f"无法解析地址: {server_addr}")
    except dns.resolver.LifetimeTimeout:
        logger.warning(f"DNS 超时: {server_addr}")
    except OSError:
        logger.warning(f"连接错误: {server_addr}")
        status_data[server_name] += 1
    else:
        if status_data[server_name] >= fail_count:
            add_msg(restoration_message_seg)
        status_data[server_name] = 0
    finally:
        if status_data[server_name] == fail_count:
            add_msg(warning_message_seg)
        logger.trace(f"检测完成: {server_name}->{status_data[server_name]}")


async def send_msg(message: Message):
    for group in groups:
        await get_bot().call_api("send_message", channel=group, message=message)


@scheduler.scheduled_job(trigger="cron", second="0")
async def check():
    logger.trace("检测中...")
    message = Message()

    def add_msg(message_seg: MessageSegment):
        message.append(message_seg)

    tasks = [
        asyncio.create_task(check_server(server_name, add_msg))
        for server_name in server_data
    ]
    await asyncio.wait(tasks) if tasks else ...
    logger.trace(f"检测完成 -> {status_data}")
    if not message:
        return
    await send_msg(message)
