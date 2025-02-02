from nonebot import get_plugin_config, require
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata, on_command
from nonebot.rule import Rule

from .config import Config

require("xas_util")
from ..xas_util import (  # pylint: disable=C0411,C0413,E0402  # noqa: E402
    rule_check_trust,
)

__plugin_meta__ = PluginMetadata(
    name="xas_ping",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

Ping = on_command("ping", rule=Rule(rule_check_trust), permission=SUPERUSER)


@Ping.handle()
async def pong(matcher: Matcher):
    await matcher.finish("pong")
