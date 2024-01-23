from nonebot import get_driver
from nonebot.plugin import on_command
from nonebot.params import EventMessage, CommandArg
from nonebot.adapters.red.bot import Bot
from nonebot.adapters.red.message import Message, MediaMessageSegment
import httpx
import filetype

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)


trace = on_command("识别人物", aliases={"人物识别", "这是谁", "这谁"})


async def traceImage(imageData: bytes):
    imageType = filetype.guess(imageData)

    if imageType is None:
        await trace.finish("错误: 无法识别图片类型")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://aiapiv2.animedb.cn/ai/api/detect?force_one=1&model=anime&ai_detect=0",
                files={"image": (f"image.{imageType.extension}", imageData, imageType.mime)},
            )
        except Exception as e:
            await trace.finish(f"错误: {e.__class__.__name__}{e}")
    result = response.json()

    if result["code"] != 0:
        await trace.finish(f"错误: code{result['code']}")

    # TODO
    resultList: list = result["data"][0]["char"]
    resultList = sorted(resultList, key=lambda it: it["acc"], reverse=True)[:5]

    resultMessage = Message()
    resultMessage.append("设别完成\n可能的角色:\n")
    for i in range(len(resultList)):
        role = resultList[i]
        resultMessage.append(f"{i+1}. {role['name']}\n")
        resultMessage.append(f"    来自: {role['cartoonname']}\n")
        resultMessage.append(f"    置信度: {role['acc']}\n")

    await trace.finish(resultMessage)


@trace.handle()
async def _(
    bot: Bot,
    args: Message = CommandArg(),
):
    if not (imageMessage := args.get("image")):
        return

    imageMessageSegment: MediaMessageSegment = imageMessage[0]  # type: ignore
    imageData = await imageMessageSegment.download(bot)

    await traceImage(imageData)


@trace.got("image", prompt="请发照片")
async def _(bot: Bot, args: Message = EventMessage()):
    print("收到照片", args)

    if not (imageMessage := args.get("image")):
        await trace.finish("未找到图片")

    print("image message", imageMessage)

    imageMessageSegment: MediaMessageSegment = imageMessage[0]  # type: ignore
    imageData = await imageMessageSegment.download(bot)

    await traceImage(imageData)
