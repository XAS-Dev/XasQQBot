from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""

    xas_checkmc_servers: dict[str, str]
    xas_checkmc_groups: list[str]
