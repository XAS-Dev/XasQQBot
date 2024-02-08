import hashlib
import time
import re

from nonebot import get_driver
from nonebot.plugin import PluginMetadata, require
from nonebot.plugin import on_message
from nonebot.params import EventPlainText
from nonebot.matcher import Matcher
from nonebot.adapters.satori.event import MessageCreatedEvent
from nonebot.adapters.satori.message import MessageSegment, Message
import httpx

from .config import Config

require("xas_util")

from ..xas_util import (  # pylint: disable=E0402,C0413  # noqa: E402
    create_quote_or_at_message,
)

__plugin_meta__ = PluginMetadata(
    name="xas_github_opengraph",
    description="",
    usage="",
    config=Config,
)

global_config = get_driver().config
config = Config.parse_obj(global_config)
host_mode = config.github_opengraph_host_mode


GithubMessage = on_message()


@GithubMessage.handle()
async def _(
    matcher: Matcher,
    event: MessageCreatedEvent,
    message_text=EventPlainText(),
):
    result = re.findall(
        r"github.com/([a-zA-Z0-9-]+/[a-zA-Z0-9-/.]+)",
        message_text,
    )
    if not result:
        return

    async with httpx.AsyncClient(timeout=60, verify=not host_mode) as client:
        if host_mode:
            response = await client.get(
                f"https://{config.xas_github_opengraph_githubassets_host}/{hashlib.sha256(str(time.time()).encode())}/{result[0]}",
                headers={"Host": "opengraph.githubassets.com"},
            )
        else:
            response = await client.get(
                f"https://opengraph.githubassets.com/{hashlib.sha256(str(time.time()).encode())}/{result[0]}"
            )
        result_message = Message()
        result_message.append(create_quote_or_at_message(event))
        result_message.append(
            MessageSegment.image(raw={"data": response.content, "mime": "image/png"})
        )
        await matcher.finish(result_message)
