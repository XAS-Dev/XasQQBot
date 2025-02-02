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
        reasoning = response.choices[0].message.model_dump().get("reasoning_content", None)
        logger.debug(f"推理过程 -> {reasoning}")
        return answer, [*messages, {"role": "assistant", "content": answer}]  # type: ignore


# a = {
#     "id": "7bcc9d5f-23df-4b0f-bbf3-febf0da8aa3a",
#     "object": "chat.completion",
#     "created": 1738489270,
#     "model": "deepseek-reasoner",
#     "choices": [
#         {
#             "index": 0,
#             "message": {
#                 "role": "assistant",
#                 "content": "Hello! How can I assist you today?",
#                 "reasoning_content": 'Okay, the user started with "Hello!" which is a common greeting. I should respond in a friendly and welcoming manner. Let me make sure to keep it open-ended so they feel comfortable asking for help. Maybe say something like, "Hello! How can I assist you today?" That\'s straightforward and inviting.',
#             },
#             "logprobs": null,
#             "finish_reason": "stop",
#         }
#     ],
#     "usage": {
#         "prompt_tokens": 13,
#         "completion_tokens": 74,
#         "total_tokens": 87,
#         "prompt_tokens_details": {"cached_tokens": 0},
#         "completion_tokens_details": {"reasoning_tokens": 63},
#         "prompt_cache_hit_tokens": 0,
#         "prompt_cache_miss_tokens": 13,
#     },
#     "system_fingerprint": "fp_7e73fd9a08",
# }
