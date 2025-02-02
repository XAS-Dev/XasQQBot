from pydantic import BaseModel


class Config(BaseModel):
    """Plugin Config Here"""

    xas_checkmc_servers: dict[str, str]
    xas_checkmc_groups: list[str]
    xas_checkmc_fail_count: int = 3
