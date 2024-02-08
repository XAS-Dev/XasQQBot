# XAS-QQBot-v2

XAS Minecraft 服务器 QQ 群机器人

## 功能

- [x] AnimeTrace 动漫人物识别
- [x] Github 项目卡片
- [ ] Github commits 消息推送
- [ ] ChatGPT 聊天
- [ ] 获取 MC 服务器状态

## 如何使用

### 直接运行

使用 `pip install .` 或 `pdm install` 安装依赖

使用 `nb run --reload` 运行机器人

### 使用Docker

```bash
docker run \
    --name xas_bot \
    -e SATORI_CLIENTS="[
        {
            \"host\": \"localhost\",
            \"port\": \"5500\",
            \"path\": \"\",
            \"token\": \"xxx\"
        }
    ]" \
    -e SUPERUSERS=[] \
    -e XAS_TRUSTED_CHANNEL=[\"12345678\",\"private:12345678\"] \
    -e XAS_CHATGPT_ENABLE_CHANNEL=[\"12345678\",\"private:12345678\"] \
    -e XAS_CHATGPT_API="api.example\v1" \
    -e XAS_CHATGPT_KEY=\"sk-*****\" \
    -e XAS_CHATGPT_DEFAULT_MODEL=\"gpt-3.5-turbo\" \
    -e XAS_CHATGPT_DEFAULT_PROMPT=\"example prompt\" \
    -e XAS_CHATGPT_CONTENT_VALIDITY_PERIOD=1200 \
    xiyang6666/xas_qqbot:2.0.0
```

## 文档

详见 [NoneBot Docs](https://nonebot.dev/)
