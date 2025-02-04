from dataclasses import dataclass
from typing import Any, Callable, Coroutine


@dataclass
class ChatInitEvent:
    session_id: str
    system_prompt: str


@dataclass
class ChatAskEvent:
    session_id: str
    message: str
    try_times: int = 1


@dataclass
class ChatAnswerEvent:
    session_id: str
    message: str


chat_init_listener: list[Callable[[ChatInitEvent], Coroutine[Any, Any, None]]] = []
chat_ask_listener: list[Callable[[ChatAskEvent], Coroutine[Any, Any, None]]] = []
chat_answer_listener: list[Callable[[ChatAnswerEvent], Coroutine[Any, Any, None]]] = []


def on_chat_init(listener: Callable[[ChatInitEvent], Coroutine[Any, Any, None]]):
    chat_init_listener.append(listener)


def on_chat_ask(listener: Callable[[ChatAskEvent], Coroutine[Any, Any, None]]):
    chat_ask_listener.append(listener)


def on_chat_answer(listener: Callable[[ChatAnswerEvent], Coroutine[Any, Any, None]]):
    chat_answer_listener.append(listener)
