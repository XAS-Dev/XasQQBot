from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""

    xas_gpt_mcstatus_server_host: str
    xas_gpt_mcstatus_server_port: int
