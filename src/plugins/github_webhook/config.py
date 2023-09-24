from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""

    webhook_enable_group: list[str]
    webhook_secret_token: str
