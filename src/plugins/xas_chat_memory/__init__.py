import json
import re
from datetime import datetime
from typing import TypedDict

from nonebot import get_plugin_config, require
from nonebot.plugin import PluginMetadata

from .config import Config

require("nonebot_plugin_localstore")
from nonebot_plugin_localstore import (  # pylint: disable=C0411,C0413,E0402  # noqa: E402
    get_data_dir,
)

require("xas_chatgpt")
from ..xas_chatgpt.api import (  # pylint: disable=C0411,C0413,E0402  # noqa: E402
    ChatAnswerEvent,
    ChatAskEvent,
    ChatInitEvent,
    on_chat_answer,
    on_chat_ask,
    on_chat_init,
)

__plugin_meta__ = PluginMetadata(
    name="xas_chat_memory",
    description="",
    usage="",
    config=Config,
)


class Memory(TypedDict):
    time: datetime
    content: str


config = get_plugin_config(Config)

data_dir = get_data_dir(__plugin_meta__.name)
chat_memory_file_dir = data_dir / "chat_memory.json"
chat_memory: list[Memory] = []


def save_chat_memory():
    w_data = [
        {
            "time": memory["time"].isoformat(),
            "content": memory["content"],
        }
        for memory in chat_memory
    ]
    with open(chat_memory_file_dir, "w", encoding="utf-8") as fw:
        json.dump(w_data, fw, indent=4, ensure_ascii=False)


if chat_memory_file_dir.exists():
    with open(chat_memory_file_dir, "r", encoding="utf-8") as fr:
        r_data = json.load(fr)
    chat_memory = [
        {
            "time": datetime.fromisoformat(memory["time"]),
            "content": memory["content"],
        }
        for memory in r_data
    ]
else:
    save_chat_memory()


async def chat_init_listener(event: ChatInitEvent):
    event.system_prompt = event.system_prompt.replace("{memories}", "\n".join([f"- {memory['time']}: {memory['content']}" for memory in chat_memory]))


on_chat_init(chat_init_listener)


async def chat_ask_listener(event: ChatAskEvent):
    event.message = f"现在时间是{datetime.now()}\n{event.message}"


on_chat_ask(chat_ask_listener)


async def chat_answer_listener(event: ChatAnswerEvent):
    new_memory: list[Memory] = []
    for memory in re.finditer(r"#记忆 (.*)", event.message):
        new_memory.append({"content": memory.group(1), "time": datetime.now()})
    if new_memory:
        chat_memory.extend(new_memory)
        save_chat_memory()
    event.message = re.sub(r"#记忆 .*", "", event.message)


on_chat_answer(chat_answer_listener)
