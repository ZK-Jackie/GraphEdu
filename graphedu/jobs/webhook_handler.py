"""Webhook 处理入口函数

处理 Webhook 类型的定时任务调用
"""

import hashlib
import hmac
import json
import logging

import httpx

logger = logging.getLogger(__name__)


async def webhook_entry(job_id: int, webhook_url: str, webhook_secret: str, *args, **kwargs):
    """Webhook 调用入口函数

    发送 HTTP POST 请求到指定的 Webhook URL

    Args:
        job_id: 任务ID
        webhook_url: Webhook URL
        webhook_secret: Webhook 密钥（用于签名）
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        dict: 执行结果

    Raises:
        Exception: Webhook 调用失败时抛出
    """
    logger.info(f"开始执行 Webhook 任务: job_id={job_id}, url={webhook_url}")

    try:
        # 构建请求体
        payload = {
            "job_id": job_id,
            "args": args,
            "kwargs": kwargs,
        }

        # 序列化为 JSON
        body = json.dumps(payload, ensure_ascii=False)

        # 计算签名
        signature = None
        if webhook_secret:
            signature = hmac.new(
                webhook_secret.encode("utf-8"),
                body.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

        # 发送 HTTP POST 请求
        headers = {
            "Content-Type": "application/json",
        }
        if signature:
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(webhook_url, headers=headers, content=body)

            # 检查响应状态
            response.raise_for_status()

            result = {
                "status": "success",
                "message": "Webhook 调用成功",
                "response_status": response.status_code,
                "response_body": response.text,
            }

            logger.info(f"Webhook 任务执行成功: job_id={job_id}, status={response.status_code}")
            return result

    except httpx.HTTPError as e:
        error_msg = f"Webhook HTTP 请求失败: {e}"
        logger.error(f"Webhook 任务执行失败: job_id={job_id}, error={error_msg}")
        raise Exception(error_msg) from e
    except Exception as e:
        error_msg = f"Webhook 调用失败: {e}"
        logger.error(f"Webhook 任务执行失败: job_id={job_id}, error={error_msg}")
        raise Exception(error_msg) from e
