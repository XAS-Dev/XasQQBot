import re
import hashlib
import time

from nonebot import get_driver, get_bot
from nonebot.plugin.on import on_message
from nonebot.adapters.red.bot import Bot
from nonebot.adapters.red.event import GroupMessageEvent
from nonebot.adapters.red.message import MessageSegment
import httpx

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)  # type: Config

message = on_message(priority=1, block=False)


@message.handle()
async def _(event: GroupMessageEvent):
    result = re.findall(
        r"(?:https://|http://|^|(?![a-zA-Z0-9-._]))github.com/([a-zA-Z0-9-]+/[a-zA-Z0-9-/.]+)",
        event.get_plaintext(),
    )
    if not result:
        return
    bot: Bot = get_bot()  # type: ignore

    async with httpx.AsyncClient(
        timeout=60, verify=not config.github_card_host_mode
    ) as client:
        if config.github_card_host_mode:
            response = await client.get(
                f"https://{config.github_card_githubassets_host}/{hashlib.sha256(str(time.time()).encode())}/{result[0]}",
                headers={"Host": "opengraph.githubassets.com"},
            )
        else:
            response = await client.get(
                f"https://opengraph.githubassets.com/{hashlib.sha256(str(time.time()).encode())}/{result[0]}"
            )
        await message.send(MessageSegment.image(response.content))
