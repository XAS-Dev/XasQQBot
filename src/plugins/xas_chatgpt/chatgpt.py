import json
import re
import sys
import urllib.parse
from typing import List, Tuple, TypedDict

from httpx import AsyncClient, Timeout
from nonebot import get_plugin_config
from nonebot.log import default_filter, default_format, logger, logger_id
from tqdm import tqdm

from .config import Config

config = get_plugin_config(Config)

logger.remove(logger_id)
logger.add(
    sys.stdout,
    level=0,
    diagnose=False,
    filter=(lambda record: default_filter(record) and not getattr(tqdm, "_instances")),
    format=default_format,
)
logger.add(
    lambda msg: tqdm.write(msg, end=""),
    level=0,
    diagnose=False,
    filter=(lambda record: default_filter(record) and getattr(tqdm, "_instances")),
    format=default_format,
    colorize=True,
)


class ChatCompletionMessage(TypedDict):
    role: str
    content: str


class ChatGPT:
    @classmethod
    async def chat(
        cls,
        message: str,
        context: List[ChatCompletionMessage],
        system_prompt: str,
        model: str = "gpt-3.5-turbo",
        name: str = "chatgpt",
    ) -> Tuple[str, List[ChatCompletionMessage]]:
        messages = [
            *context,
            {"role": "user", "content": message},
        ]
        logger.trace("调用ChatGPT")
        logger.trace(f"模型:{model}")
        logger.trace(f"系统提示:{system_prompt}")
        logger.trace(f"上下文:{context}")
        logger.trace(f"消息:{message}")
        async with AsyncClient(timeout=Timeout(None, connect=10, write=10, read=60)) as client:
            async with client.stream(
                "POST",
                urllib.parse.urljoin(config.xas_chatgpt_api, "chat/completions"),
                json={
                    "model": model,
                    "messages": [{"role": "system", "content": system_prompt}, *messages],
                    "stream": True,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {config.xas_chatgpt_key}",
                },
            ) as response:
                response.raise_for_status()
                reasoning_message = ""
                answer_message = ""
                with tqdm(
                    total=None,
                    unit="char",
                    dynamic_ncols=True,
                    leave=False,
                    postfix=f"{model} {name}",
                ) as pbar:
                    async for line in response.aiter_lines():
                        if not line:
                            pbar.update(0)
                            continue
                        result = re.match(r"^data: (.*)$", line)
                        if not result:
                            raise ValueError(f"Invalid response: {line}")
                        line_data = result.group(1)
                        if line_data in [": keep-alive", "[DONE]"]:
                            pbar.update(0)
                            continue
                        json_data = json.loads(line_data)
                        if not json_data["choices"]:
                            pbar.update(0)
                            continue
                        reasoning_content = json_data["choices"][0]["delta"].get("reasoning_content")
                        answer_content = json_data["choices"][0]["delta"].get("content")
                        if reasoning_content:
                            reasoning_message += reasoning_content
                            pbar.update(len(reasoning_content))
                        if answer_content:
                            answer_message += answer_content
                            pbar.update(len(answer_content))
        if not (reasoning_message or answer_message):
            raise TimeoutError("API繁忙")

        if not reasoning_message:
            match_result = re.match(r"^<think>(.*)</think>(.*)$", answer_message, flags=re.DOTALL)
            if not match_result:
                raise ValueError(f"Invalid response:\n{answer_message}")
            reasoning_message = match_result.group(1).strip()
            answer_message = match_result.group(2).strip()

        logger.trace("ChatGPT调用结束")
        logger.debug(f"推理过程 -> {reasoning_message}")
        logger.debug(f"原始回答: {answer_message}")
        return answer_message, [*messages, {"role": "assistant", "content": answer_message}]  # type: ignore
