import re
import hashlib
import time

from nonebot import get_driver
from nonebot.plugin.on import on_message
from nonebot.adapters.red.event import GroupMessageEvent
from nonebot.adapters.red.message import MessageSegment
import httpx

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)

message = on_message(priority=1, block=False)


@message.handle()
async def _(event: GroupMessageEvent):
    result = re.findall(
        r"(?:https://|http://|^|(?![a-zA-Z0-9-._]))github.com/([a-zA-Z0-9-]+/[a-zA-Z0-9-/.]+)",
        event.get_plaintext(),
    )
    if not result:
        return

    async with httpx.AsyncClient(
        timeout=60, verify=not config.github_card_host_mode  # type: ignore
    ) as client:
        if config.github_card_host_mode:  # type: ignore
            response = await client.get(
                f"https://{config.github_card_githubassets_host}/{hashlib.sha256(str(time.time()).encode())}/{result[0]}",  # type: ignore  # noqa: E501
                headers={"Host": "opengraph.githubassets.com"},
            )
        else:
            response = await client.get(
                f"https://opengraph.githubassets.com/{hashlib.sha256(str(time.time()).encode())}/{result[0]}"
            )
        await message.send(MessageSegment.image(response.content))
