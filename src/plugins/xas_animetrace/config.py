from typing import Dict

from pydantic import BaseModel
from typing_extensions import TypedDict


class AnimetraceModel(TypedDict):
    index: int
    name: str


class AnimetraceModelConfig(TypedDict):
    anime: Dict[str, str]
    game: Dict[str, str]


class Config(BaseModel):
    """Plugin Config Here"""

    xas_animetrace_model: AnimetraceModelConfig = {
        "anime": {
            "anime": "低准确率动漫模型",
            "anime_model_lovelive": "高准确率公测动漫模型",
            "pre_stable": "高准确率动漫模型",
        },
        "game": {
            "game": "低准确率GalGame模型",
            "game_model_kirakira": "高准确率GalGame模型",
        },
    }
