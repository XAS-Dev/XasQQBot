from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""

    github_card_host_mode: bool = False  # 直接请求ip地址并带上host头部, 防止dns污染
    github_card_githubassets_host:str = "185.199.110.154"
