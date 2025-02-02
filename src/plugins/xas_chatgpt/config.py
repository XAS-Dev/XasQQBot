from pydantic import BaseModel


class Config(BaseModel):
    """Plugin Config Here"""

    xas_chatgpt_enable_channel: list = []
    xas_chatgpt_api: str
    xas_chatgpt_key: str
    xas_chatgpt_default_model: str = "gpt-3.5-turbo"
    xas_chatgpt_advanced_model: str = "gpt-4-turbo"
    xas_chatgpt_default_prompt: str = (
        "你是XAS bot, 是一个QQ群聊中的成员. "
        "群聊中的其他成员会与你聊天, 你会收到格式为 “用户名(uid): 消息” 的信息, 请尝试回复与你聊天的成员. "
        "你应当使用使用**中文**回答问题, 用户名中可能包含其他语言的文字, 注意**不要通过用户名推断用户使用的语言**."
        "注意请直接回复消息, 不要包含前缀. "
    )
    xas_chatgpt_context_validity_period: int = 1200
