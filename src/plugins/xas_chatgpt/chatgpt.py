from typing import List, Tuple

from nonebot import get_plugin_config
from nonebot.log import logger
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from .config import Config

config = get_plugin_config(Config)


class ChatGPT:
    @classmethod
    async def chat(
        cls,
        message: str,
        context: List[ChatCompletionMessageParam],
        system_prompt: str,
        model: str = "gpt-3.5-turbo",
    ) -> Tuple[str, List[ChatCompletionMessageParam]]:
        client = AsyncOpenAI(
            api_key=config.xas_chatgpt_key,
            base_url=config.xas_chatgpt_api,
            timeout=60,
        )
        messages = [
            *context,
            {"role": "user", "content": message},
        ]
        logger.trace(f"{message}; {messages}; {system_prompt}")
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, *messages],
        )
        answer = response.choices[0].message.content
        return answer, [*messages, {"role": "assistant", "content": answer}]  # type: ignore
