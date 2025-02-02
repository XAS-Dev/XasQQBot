from pydantic import BaseModel


class Config(BaseModel):
    """Plugin Config Here"""

    xas_gpt_mcstatus_server_host: str
    xas_gpt_mcstatus_server_port: int
