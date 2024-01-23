import asyncio
import json
import hmac
import hashlib

from nonebot import get_driver, get_bot
from nonebot.drivers import Request, Response, URL, HTTPServerSetup, ASGIMixin
from nonebot.adapters.red.bot import Bot

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)


def verify_signature(payload_body, secret_token: str, signature_header: str):
    """Verify that the payload was sent from GitHub by validating SHA256.

    Raise and return 403 if not authorized.

    Args:
        payload_body: original request body to verify (request.body())
        secret_token: GitHub app webhook token (WEBHOOK_SECRET)
        signature_header: header received from GitHub (x-hub-signature-256)
    """
    if signature_header is None:
        return False

    hash_object = hmac.new(secret_token.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    return hmac.compare_digest(expected_signature, signature_header)


async def githubWebhook(request: Request):
    if verify_signature(
        request.content,
        config.github_webhook_secret_token,
        request.headers.get("x-hub-signature-256"),  # type: ignore
    ):
        data = json.loads(request.content)  # type: ignore
        message = (
            f"Github new commit from {data['head_commit']['author']['name']}\n"
            f"Repository: {data['repository']['full_name']}\n"
            f"Commit: {data['head_commit']['id'][:7]}\n"
            f"Message: {data['head_commit']['message']}\n"
            f"Link: {data['head_commit']['url']}\n"
        )
        bot: Bot = get_bot()  # type: ignore

        await bot.call_api("send_msg", message=message, group_id=request.url.query.get("group"))

        asyncio.gather(*[bot.send_group_message(groupId, message) for groupId in request.url.query.get("groups", "").split(",")])

        return Response(200, content="OK")
    else:
        return Response(401, content="Unauthorized")


driver: ASGIMixin = get_driver()  # type: ignore
driver.setup_http_server(
    HTTPServerSetup(
        path=URL("/webhook/github"),
        method="POST",
        name="hello",
        handle_func=githubWebhook,
    )
)
