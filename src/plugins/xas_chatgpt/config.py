from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""

    xas_chatgpt_enable_channel: list = []
    xas_chatgpt_api: str
    xas_chatgpt_key: str
    xas_chatgpt_default_model: str = "gpt-3.5-turbo"
    xas_chatgpt_default_prompt: str = (
        "你是XAS bot, 是一个QQ群聊中的成员. "
        "群聊中的其他成员会与你聊天, 你会收到格式为 “昵称(uid): 消息” 的信息, 请尝试回复与你聊天的成员. "
        "注意请直接回复消息, 不要包含前缀. "
    )
    xas_chatgpt_context_validity_period: int = 1200
