from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""

    repetitive_minimum = 1  # 至少重复的次数
    repetitive_limit = 5  # 消息重复到达指定次数时必然复读
    probability_index_growth = True  # 使用指数增长(关闭则为线性)
