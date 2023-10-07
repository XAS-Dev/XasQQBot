from pydantic import BaseModel, Extra
from enum import IntEnum


class ServerType(IntEnum):
    JAVA = 0
    BEDROCK = 1


class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""

    mc_host: str
    mc_port: int
    mc_type: ServerType = ServerType.JAVA
