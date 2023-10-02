from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""

    repetitive_limit = 5  # 消息重复到达指定次数时必然复读
    probability_index_growth = False  # 使用指数增长(默认线性)
