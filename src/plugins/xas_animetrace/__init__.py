from typing import Dict, List, Tuple
from urllib.parse import urlparse
from io import BytesIO
import re

from nonebot import get_driver
from nonebot.plugin import on_command, require
from nonebot.params import EventMessage, CommandArg, EventPlainText
from nonebot.plugin import PluginMetadata
from nonebot.matcher import Matcher
from nonebot.adapters.satori.message import Message, MessageSegment
from nonebot.adapters.satori.message import Image as ImageMessage
from nonebot.adapters.satori.event import MessageCreatedEvent
from nonebot.adapters.satori.bot import Bot
from typing_extensions import TypedDict
from PIL import Image
import filetype
import httpx

from .config import Config, AnimetraceModelConfig

xas_util = require("xas_util")

from ..xas_util import (  # pylint: disable=E0402,C0413  # noqa: E402
    create_quote_or_at_message,
    rule_check_trust,
)

__plugin_meta__ = PluginMetadata(
    name="xas_animetrace",
    description="",
    usage="",
    config=Config,
)

global_config = get_driver().config
config = Config.parse_obj(global_config)
models = config.xas_animetrace_model


class ApiResultChar(TypedDict):
    name: str
    cartoonname: str
    acc: float


class ApiResultItem(TypedDict):
    box: List[float]
    box_id: str
    char: List[ApiResultChar]


class ApiResult(TypedDict):
    ai: bool
    code: int
    data: List[ApiResultItem]


def clip_image(original_image: bytes, relative_box: Tuple[float, ...]):
    image = Image.open(BytesIO(original_image)).convert("RGB")
    box = (
        relative_box[0] * image.width,
        relative_box[1] * image.height,
        relative_box[2] * image.width,
        relative_box[3] * image.height,
    )
    new_image = image.crop(box)  # type: ignore
    new_image_bytes = BytesIO()
    new_image.save(new_image_bytes, format="jpeg")
    return new_image_bytes.getvalue()


def create_got_model_message(model_config: AnimetraceModelConfig):
    result_message = Message()
    result_message.append("请选择模型:\n")
    result_message.append("  动漫模型:\n")
    index = 1
    index_model_dict: Dict[int, str] = {}
    for model_id, model_name in model_config["anime"].items():
        result_message.append(f"    {index}. {model_name}\n")
        index_model_dict[index] = model_id
        index += 1
    result_message.append("  GalGame模型:\n")
    for model_id, model_name in model_config["game"].items():
        result_message.append(f"    {index}. {model_name}\n")
        index_model_dict[index] = model_id
        index += 1
    return result_message, index_model_dict


got_model_message, model_dict = create_got_model_message(config.xas_animetrace_model)


def create_trace_result_message(trace_result: ApiResult, original_image: bytes):
    if trace_result["code"] != 0:
        return Message(f"api结果错误, 错误代码: {trace_result['code']}")

    if len(trace_result["data"]) == 0:
        return Message("未识别到角色.")
    elif len(trace_result["data"]) == 1:
        result_message = Message()
        result_message.append("可能的角色:\n")
        char_list = sorted(
            trace_result["data"][0]["char"], key=lambda it: it["acc"], reverse=True
        )[:5]
        for i, probability in enumerate(char_list):
            result_message.append(f"{i+1}. {probability['name']}\n")
            result_message.append(f"    来自: {probability['cartoonname']}\n")
            result_message.append(f"    置信度: {probability['acc']}\n")
        return result_message
    else:
        result_message = Message()
        result_message.append(f"共识别到 {len(trace_result['data'])} 个角色. \n")
        for char in trace_result["data"]:
            box = tuple(char["box"][:4])
            image_data = clip_image(original_image, box)
            result_message.append(
                MessageSegment.image(raw={"data": image_data, "mime": "image/jpeg"})
            )
            result_message.append("可能的角色:\n")
            char_list = sorted(char["char"], key=lambda it: it["acc"], reverse=True)[:3]
            for i, probability in enumerate(char_list):
                result_message.append(f"{i+1}. {probability['name']}\n")
                result_message.append(f"    来自: {probability['cartoonname']}\n")
                result_message.append(f"    置信度: {probability['acc']}\n")
        return result_message


async def get_image(image_segment: ImageMessage, bot: Bot):
    parse_result = urlparse(image_segment.data["src"])
    async with httpx.AsyncClient() as client:
        print(
            f"{parse_result.scheme}://{bot.info.host}:{bot.info.port}{parse_result.path}"
        )
        response = await client.get(
            f"{parse_result.scheme}://{bot.info.host}:{bot.info.port}{parse_result.path}"
        )
    return response.read()


async def post_api(image_data: bytes, model: str) -> ApiResult:
    image_type = filetype.guess(image_data)

    if image_type is None:
        await Trace.finish("错误: 无法识别图片类型")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://aiapiv2.animedb.cn/ai/api/detect?force_one=1&model={model}&ai_detect=0",
            files={
                "image": (
                    f"image.{image_type.extension}",
                    image_data,
                    image_type.mime,
                )
            },
        )
    return response.json()


Trace = on_command(
    "animetrace",
    aliases={"人物识别", "识别人物", "这谁", "这人谁"},
    rule=rule_check_trust,
)


@Trace.handle()
async def _(
    matcher: Matcher,
    event: MessageCreatedEvent,
    args: Message = CommandArg(),
):
    print()
    if image_message := args.get("img"):
        matcher.set_arg("image", image_message)
    else:
        # 请求图片
        result_message = Message()
        result_message.append(create_quote_or_at_message(event))
        result_message.append("请发送图片.")
        await matcher.send(result_message)
        return


@Trace.got("image")
async def got_image(
    matcher: Matcher,
    event: MessageCreatedEvent,
    message=EventMessage(),
    message_text=EventPlainText(),
):
    if message_text == "退出":
        await matcher.finish(create_quote_or_at_message(event) + "已结束会话")
    image_message = message.get("img")
    if not image_message:
        await matcher.reject("无法获取图片, 请重新发送. 输入“退出”结束会话.")
    matcher.set_arg("image", image_message)
    # 请求模型
    await matcher.send(Message(create_quote_or_at_message(event)) + got_model_message)


@Trace.got("model")
async def got_model(
    matcher: Matcher,
    event: MessageCreatedEvent,
    bot: Bot,
    message_text=EventPlainText(),
):
    if (
        not re.match("^[0-9]+$", message_text)
        or (model_index := int(message_text)) not in model_dict
    ):
        await matcher.reject("请输入正确的序号. 输入“退出”结束会话. ")

    model = model_dict[model_index]
    image_message = matcher.get_arg("image")
    image_segment: ImageMessage = image_message and image_message[0]  # type: ignore
    image_data = await get_image(image_segment, bot)
    try:
        trace_result = await post_api(image_data, model)
    except httpx.ReadTimeout:
        await matcher.finish("错误: HTTP超时")
    except httpx.ConnectError:
        await matcher.finish("错误: HTTP连接错误")
    except httpx.HTTPStatusError as e:
        await matcher.finish(f"错误: HTTP状态错误: {e.response.status_code}")

    await matcher.finish(
        create_quote_or_at_message(event)
        + create_trace_result_message(trace_result, image_data)
    )
