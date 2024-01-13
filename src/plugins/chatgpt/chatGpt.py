from pathlib import Path
from datetime import datetime, timedelta
from typing import TypedDict, Optional
import json
import time
import asyncio

from nonebot import get_driver, require
from nonebot.log import logger
import openai

from .config import Config

require("mc_status")

from src.plugins.mc_status import getStatus, McStatus  # noqa: E402


class Conversation(TypedDict):
    role: str
    user: str
    content: str


class ConversationRecord(TypedDict):
    conversation: list
    last_time: datetime
    mcstatus: Optional[McStatus]
    model: str


global_config = get_driver().config
config = Config.parse_obj(global_config)

formatDict = {
    "chatgpt_owner_uid": config.chatgpt_owner_uid,
    "chatgpt_owner_nickname": config.chatgpt_owner_nickname,
}


class ChatGPT:
    def __init__(self):
        openai.api_base = config.chatgpt_api
        openai.api_key = config.chatgpt_key
        self.conversationRecordList: dict[str, ConversationRecord] = {}
        self.chatLocks: dict[str, asyncio.Lock] = {}
        self.systemPrompt: str = config.chatgpt_system_prompt
        self.dataPath = Path("conversation/")
        self.dataPath.mkdir(parents=True, exist_ok=True)
        self.load()

    def checkConversationTimeout(self, userId):
        if not (
            datetime.now() - timedelta(seconds=config.chatgpt_chat_time_limit)
            < self.getRecord(userId)["last_time"]
            < datetime.now()
        ):
            self.getRecord(userId)["conversation"] = []
            self.save()
            return True
        return False

    def getRecord(self, userId):
        # 没有记录,添加
        if userId not in self.conversationRecordList:
            # print("not in")
            self.conversationRecordList[userId] = {
                "conversation": [],
                "last_time": datetime.now(),
                "mcstatus": None,
                "model": "gpt-3.5-turbo",
            }
        return self.conversationRecordList[userId]

    async def chat(
        self, userId: str, msg: str
    ) -> tuple[Optional[str], Optional[Exception]]:
        # 加锁等待上一个完成
        if userId not in self.chatLocks:
            # 没锁，新建一个
            self.chatLocks[userId] = asyncio.Lock()
        await self.chatLocks[userId].acquire()  # 加锁

        isTimeOut = self.checkConversationTimeout(userId)

        # 生成状态提示
        statusPrompt = None
        try:
            mcStatus = await getStatus()
        except Exception as e:
            logger.error(e)
            statusPrompt = (
                f"状态改变了,目前暂时无法获取你的状态。错误原因是:{e}。如果有人询问你的状态请回答暂时发生了错误。\n"  # noqa: E501
            )
        else:
            if (
                mcStatus != self.getRecord(userId)["mcstatus"]
            ) or isTimeOut:
                self.getRecord(userId)["mcstatus"] = mcStatus
                statusPrompt = (
                    f"状态改变了,根据最新状态你目前有{mcStatus['player']['online']}/{mcStatus['player']['max']}人在线"
                    + (
                        f",他们分别为:{','.join(mcStatus['player']['sample'])}"  # type: ignore
                        if mcStatus["player"].get("sample")
                        else ""
                    )
                    + "。\n"  # type: ignore
                )
        msg = (statusPrompt or "") + msg

        # 复制纪录,成功则用复制的记录更改原纪录,失败则仍使用原纪录
        tempList = self.getRecord(userId)["conversation"].copy()
        tempList.append({"role": "user", "content": msg})

        # 开始提问
        logger.debug(f"\nasked ChatGPT:\n{msg}")
        startTime = time.time()
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.getRecord(userId)["model"],
                messages=[
                    {
                        "role": "system",
                        "content": self.systemPrompt.format_map(formatDict),
                    },
                    *tempList,
                ],
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
        self.getRecord(userId)["conversation"] = tempList
        self.getRecord(userId)["last_time"] = datetime.now()
        self.save()  # 保存
        logger.debug(
            "\n"
            f"ChatGPT answered:\n{answer}\n"
            f"-> spend time:\t {time.time() - startTime:.2f}s\n"
            f"-> spend token:\t {response['usage']['total_tokens']}"  # type: ignore
        )
        return answer, None

    def save(self):
        for key in self.conversationRecordList:
            with open(self.dataPath / f"{key}.json", "w", encoding="utf-8") as f:
                tempDict = self.conversationRecordList[key].copy()
                tempDict["last_time"] = str(tempDict["last_time"])  # type: ignore
                json.dump(tempDict, f, ensure_ascii=False)

    def load(self):
        for file in self.dataPath.iterdir():
            with open(file, "r", encoding="utf-8") as f:
                self.conversationRecordList[file.stem] = json.load(f)
                self.conversationRecordList[file.stem][
                    "last_time"
                ] = datetime.fromisoformat(
                    self.conversationRecordList[file.stem]["last_time"]  # type: ignore
                )


chatGpt = ChatGPT()
