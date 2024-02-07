from typing import List

from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""

    xas_trusted_channel: List[str] = [] # 允许的群聊/私聊, 列表中为群号或“private:”加QQ号.
