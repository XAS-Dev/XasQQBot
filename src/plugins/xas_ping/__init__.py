from nonebot import get_driver, require
from nonebot.rule import Rule
from nonebot.matcher import Matcher
from nonebot.plugin import PluginMetadata
from nonebot.plugin import on_command

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

global_config = get_driver().config
config = Config.parse_obj(global_config)

Ping = on_command("ping", rule=Rule(rule_check_trust))


@Ping.handle()
async def pong(matcher: Matcher):
    await matcher.send("pong")
