from typing import List, Tuple

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from nonebot import get_driver
from nonebot.log import logger

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)


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
            api_key=config.xas_chatgpt_key, base_url=config.xas_chatgpt_api
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
