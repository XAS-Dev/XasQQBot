from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""

    github_webhook_enable_group: list[str]
    github_webhook_secret_token: str
