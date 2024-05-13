from typing import Dict, List, Tuple, Optional
from io import BytesIO
import re

from nonebot import get_driver
from nonebot.plugin import on_command, require
from nonebot.params import EventMessage, EventPlainText, Depends
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_State
from nonebot.matcher import Matcher
from nonebot.adapters.satori.message import Message, MessageSegment
from nonebot.adapters.satori.message import Image as ImageMessage
from nonebot.adapters.satori.event import MessageCreatedEvent
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


class FileTypeException(Exception):
    def __init__(self, message, *, file_data: Optional[bytes]) -> None:
        super().__init__(message)
        self.file_data = file_data


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
        return Message(f"api结果错误, 错误代码: {trace_result['code']}.")

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


async def get_image(image_segment: ImageMessage):
    async with httpx.AsyncClient() as client:
        response = await client.get(image_segment.data["src"])
        response.raise_for_status()
    return response.read()


async def post_api(
    image_data: bytes,
    image_type,
    model: str,
) -> ApiResult:

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
        response.raise_for_status()
    return response.json()


Trace = on_command(
    "animetrace",
    aliases={"人物识别", "识别人物", "这谁", "这人谁"},
    rule=rule_check_trust,
)


async def depends_image_message(
    event: MessageCreatedEvent,
    message: Message = EventMessage(),
) -> Optional[Message]:
    return message.get("img") or (
        event.reply
        and (reply_content := event.reply.data.get("content"))
        and reply_content.get("img")
    )  # type: ignore


@Trace.handle()
async def trace(
    matcher: Matcher,
    event: MessageCreatedEvent,
    image_message: Optional[Message] = Depends(depends_image_message),
):
    if image_message:
        matcher.set_arg("image", image_message)
        return

    # 请求图片
    await matcher.send(create_quote_or_at_message(event) + "请发送图片.")


@Trace.got("image")
async def got_image(
    matcher: Matcher,
    event: MessageCreatedEvent,
    state: T_State,
    message_text=EventPlainText(),
    image_message: Optional[Message] = Depends(depends_image_message),
):
    if message_text == "退出":
        await matcher.finish(create_quote_or_at_message(event) + "已结束会话")

    if not image_message:
        await matcher.reject(
            create_quote_or_at_message(event)
            + "无法获取图片, 请重新发送. 输入“退出”结束会话."
        )

    image_segment: ImageMessage = image_message[0]  # type: ignore
    try:
        image_data = await get_image(image_segment)
    except httpx.HTTPStatusError as e:
        await matcher.finish(
            create_quote_or_at_message(event)
            + f"错误: 无法从QQNT获取资源: {e.response.status_code}"
        )

    image_type = filetype.guess(image_data)
    if image_type is None:
        await matcher.finish(
            create_quote_or_at_message(event) + "错误: 无法识别图片类型."
        )

    state["image_data"] = image_data
    state["image_type"] = image_type

    matcher.set_arg("image", image_message)
    await matcher.send(create_quote_or_at_message(event) + got_model_message)


@Trace.got("model")
async def got_model(
    matcher: Matcher,
    event: MessageCreatedEvent,
    state: T_State,
    message_text=EventPlainText(),
):
    if message_text == "退出":
        await matcher.finish(create_quote_or_at_message(event) + "已结束会话")

    if (
        not re.match("^[0-9]+$", message_text)
        or (model_index := int(message_text)) not in model_dict
    ):
        await matcher.reject("请输入正确的序号. 输入“退出”结束会话. ")

    model = model_dict[model_index]
    image_data = state["image_data"]
    image_type = state["image_type"]

    try:
        trace_result = await post_api(image_data, image_type, model)
    except httpx.ReadTimeout:
        await matcher.finish("错误: HTTP超时.")
    except httpx.ConnectError:
        await matcher.finish("错误: HTTP连接错误.")
    except httpx.HTTPStatusError as e:
        await matcher.finish(f"错误: HTTP状态错误: {e.response.status_code}.")

    await matcher.finish(
        create_quote_or_at_message(event)
        + create_trace_result_message(trace_result, image_data)
    )
