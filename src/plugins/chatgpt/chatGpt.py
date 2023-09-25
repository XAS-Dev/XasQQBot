from pathlib import Path
from datetime import datetime, timedelta
import json
import asyncio

from nonebot import get_driver
from nonebot.log import logger
import openai

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)


class ChatGPT:
    def __init__(self):
        openai.api_base = config.chatgpt_api
        openai.api_key = config.chatgpt_key
        self.conversationRecord = {}  # type: dict[str,dict]
        self.chatLocks = {}  # type: dict[str,asyncio.Lock]
        self.systemPrompt = config.chatgpt_system_prompt
        self.dataPath = Path("conversation/")
        self.dataPath.mkdir(parents=True, exist_ok=True)
        self.load()

    def checkConversationTimeout(self, userId):
        if self.conversationRecord[userId]["last_time"] < (
            datetime.now() - timedelta(seconds=config.chatgpt_maxlength)
        ):
            self.conversationRecord[userId]["conversation"] = []
            self.save()

    async def chat(self, userId: str, msg: str) -> tuple[str | None, Exception | None]:
        # 加锁等待上一个完成
        if userId not in self.chatLocks:
            # 没锁，新建一个
            self.chatLocks[userId] = asyncio.Lock()
        await self.chatLocks[userId].acquire()  # 加锁
        # 没有记录,添加
        if userId not in self.conversationRecord:
            self.conversationRecord[userId] = {
                "conversation": [],
                "last_time": datetime.now(),
            }
        self.checkConversationTimeout(userId)

        # 复制纪录,成功则用复制的记录更改原纪录,失败则仍使用原纪录
        tempList = self.conversationRecord[userId]["conversation"].copy()
        tempList.append({"role": "user", "content": msg})

        # 开始提问
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": self.systemPrompt}, *tempList],
                timeout=10,
            )
        except Exception as e:
            # ChatGPT错误
            logger.error(e)
            return None, e
        finally:
            self.chatLocks[userId].release()  # 解锁

        # 提问成功,获取结果并修改纪录
        answer = response.choices[0].message["content"]  # type: ignore
        tempList.append({"role": "assistant", "content": answer})
        self.conversationRecord[userId]["conversation"] = tempList
        self.conversationRecord[userId]["last_time"] = datetime.now()
        self.save()  # 保存
        return answer, None

    def save(self):
        for key in self.conversationRecord:
            with open(self.dataPath / f"{key}.json", "w", encoding="utf-8") as f:
                tempDict = self.conversationRecord[key].copy()
                tempDict["last_time"] = str(tempDict["last_time"])
                json.dump(tempDict, f, ensure_ascii=False)

    def load(self):
        for file in self.dataPath.iterdir():
            with open(file, "r", encoding="utf-8") as f:
                self.conversationRecord[file.stem] = json.load(f)
                self.conversationRecord[file.stem][
                    "last_time"
                ] = datetime.fromisoformat(
                    self.conversationRecord[file.stem]["last_time"]
                )


chatGpt = ChatGPT()
