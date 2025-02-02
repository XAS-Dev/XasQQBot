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
            timeout=30,
        )
        messages = [
            *context,
            {"role": "user", "content": message},
        ]
        logger.trace("调用ChatGPT")
        logger.trace(f"模型:{model}")
        logger.trace(f"消息:{message}")
        logger.trace(f"上下文:{context}")
        logger.trace(f"系统提示:{system_prompt}")
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, *messages],
        )
        answer = response.choices[0].message
        answer_content = response.choices[0].message.content
        reasoning = response.choices[0].message.model_dump().get("reasoning_content", None)
        logger.debug(f"推理过程 -> {reasoning}")
        logger.debug(f"原始回答: {answer_content}")
        return answer_content, [*messages, answer.model_dump()]  # type: ignore
