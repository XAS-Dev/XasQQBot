# XasQQBot

> [!TIP]
> 此项目已迁移至[XAS-QQBot-v2](https://github.com/XAS-Dev/XAS-QQBot-v2)

XAS Minecraft 服务器 QQ 群机器人

## 功能

- [x] ChatGPT 聊天
- [x] Github 项目卡片
- [ ] Github commits 消息推送
- [x] 获取 MC 服务器状态

## 如何使用

1. 在实体机中使用

   1. 使用 `pip install .` 或 `pdm install` 安装依赖
   2. 使用 `nb run --reload` 运行机器人

2. 在 docker 中使用

   1. 使用

    ```bash
    docker run \
        --name xas_bot \
        -e RED_BOTS="[
            {
                \"port\": \"YOUR_PORT\",
                \"token\": \"YOUR_TOKEN\",\
                \"host\": \"YOUR_HOST\"
            }
        ]" \
        -e  CHATGPT_KEY=\"YOUR_KEY\" \
        -e CHATGPT_OWNER=\"12345678\" \
        -e CHATGPT_ENABLE_GROUP=[\"12345678\",\"87654321\"] \
        -e CHATGPT_ENABLE_USER=[\"12345678\"] \
        -e MC_HOST=\"xasmc.xyz\" \
        -e GITHUB_WEBHOOK_SECRET_TOKEN="YOUR_TOKEN" \
        xiyang6666/xas_qqbot:0.1.0
    ```

    运行容器

## 文档

详见 [NoneBot Docs](https://nonebot.dev/)
