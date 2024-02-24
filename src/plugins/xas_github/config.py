from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""

    xas_github_opengraph_githubassets_host: str = "185.199.109.154"
    github_opengraph_host_mode: bool = True
