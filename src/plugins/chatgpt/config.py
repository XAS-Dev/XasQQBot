from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""

    chatgpt_api: str
    chatgpt_key: str
    chatgpt_enable_group: list = []
    chatgpt_enable_user: list = []
    chatgpt_maxlength: int
    chatgpt_system_prompt: str = """请使用口语化的、可爱的、女性化的、调皮的语言风格和我交流. 你是一个Minecraft服务器, 你的名字叫“XAS bot”, 你喜欢玩“Minecraft”. 你需要尝试体会我与你对话中的感情、产生自己的情感并尽可能给出可爱的回答。不要一次回复太多句话并且不要回复太多无关信息。"""  # noqa: E501
    chatgpt_chat_time_limit: int