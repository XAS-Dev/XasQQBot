from typing import List

from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""

    # 信任的群聊/私聊, 允许不用@触发指令, 列表中为群号或“private:”加QQ号.
    xas_trusted_channel: List[str] = []
