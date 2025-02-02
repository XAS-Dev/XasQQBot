import re
import urllib.parse
from typing import List

import httpx
from nonebot import get_plugin_config
from nonebot.adapters.satori.event import MessageCreatedEvent
from nonebot.adapters.satori.message import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata, on_command
from typing_extensions import TypedDict

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="xas_moegirlwiki",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)


class Page(TypedDict):
    index: int
    title: str
    categories: List[str]


Search = on_command("搜索", aliases={"mnbk"})


@Search.handle()
async def search(
    matcher: Matcher,
    event: MessageCreatedEvent,
    argv: Message = CommandArg(),
):
    search_text = None
    if event.reply:
        content_messages = event.reply.data.get("content")
        search_text = content_messages and content_messages.extract_plain_text()
    if not search_text:
        search_text = argv.extract_plain_text()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://mzh.moegirl.org.cn/api.php",
            data={
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "prop": "categories",
                "list": "search",
                "generator": "search",
                "srsearch": search_text,
                "gsrsearch": search_text,
            },
        )
    data = response.json()
    processed_data: List[Page] = []
    print(data)
    for page in data["query"]["pages"]:
        processed_data.append(
            {
                "index": page["index"],
                "title": page["title"],
                "categories": [  # type: ignore
                    (match_result := re.match(r"Category:(.*)", category["title"])) and "#" + match_result.group(1)
                    for category in page.get("categories", [])
                ],
            }
        )
    processed_data = sorted(processed_data, key=lambda item: item["index"])

    result_message = Message()
    result_message.append("猜你想搜: \n")
    for page in processed_data[:3]:
        print(page)
        result_message.append(f"{page['index']}. {page['title']}\n")
        result_message.append(f"  tag: {' '.join(page['categories'])}\n" if page["categories"] else "")
        param = f"{page['title']}"
        result_message.append(f"  https://mzh.moegirl.org.cn/{urllib.parse.quote(param)}\n\n")

    await matcher.finish(result_message)
