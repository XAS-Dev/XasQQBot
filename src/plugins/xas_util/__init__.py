from webbrowser import get

from nonebot import get_plugin_config
from nonebot.adapters.satori.event import MessageCreatedEvent
from nonebot.adapters.satori.message import MessageSegment
from nonebot.log import logger
from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="xas_util",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

trusted_channel = config.xas_trusted_channel


def create_quote_or_at_message(event: MessageCreatedEvent):
    return MessageSegment.quote(event.message.id) if event.message else MessageSegment.at(event.get_user_id(), event.member and event.member.nick)


async def rule_check_tome(event: MessageCreatedEvent):
    result = (event.channel and event.channel.id.startswith("private:")) or event.is_tome()
    logger.trace(f"rule tome/private: {result} ({event.channel}; {event.is_tome()})")
    return result


async def rule_check_trust(event: MessageCreatedEvent):
    return event.channel and event.channel.id in trusted_channel or event.is_tome()
