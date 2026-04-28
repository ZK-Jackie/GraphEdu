"""验证码接口"""

from datetime import timedelta
import logging

from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from graphedu.common.models.constants import RedisConstants
from graphedu.common.models.dto.commonv2.captcha import CaptchaDTO, TurnstileValidateDTO
from graphedu.common.models.vo.base import ResponseType, ResponseUtil
from graphedu.common.models.vo.commonv2.captcha import TurnstileValidateVO
from graphedu.common.resource import AsyncHttpClient
from graphedu.common.resource.deps import get_httpx, get_redis
from graphedu.common.utils.uuids import uuid7_str
from graphedu.services.common.captcha import CaptchaService

logger = logging.getLogger(__name__)

captcha_controller = APIRouter(prefix="/captcha")


@captcha_controller.get("/captchaImage", response_model=ResponseType[CaptchaDTO])
async def get_captcha_image(redis_client: Redis = Depends(get_redis)):
    """获取验证码图片

    返回base64编码的图片和会话ID
    """
    # 生成验证码
    captcha_image, captcha_result = await CaptchaService.create_captcha_image()

    # 生成会话ID
    session_id = uuid7_str()

    # 存储到Redis，有效期2分钟
    await redis_client.set(
        f"{RedisConstants.Common.CAPTCHA_KEY}:{session_id}", str(captcha_result), ex=timedelta(minutes=2)
    )

    logger.info(f"会话 {session_id} 获取验证码成功")

    # 返回验证码信息
    return ResponseUtil.success(
        data=CaptchaDTO(
            uuid=session_id,
            img=captcha_image,
            code=captcha_result,  # 仅测试环境返回答案
            captcha_enabled=True,
        )
    )


@captcha_controller.post("/turnstile/validate", response_model=ResponseType[TurnstileValidateVO])
async def validate_cloudflare_turnstile(
    data: TurnstileValidateDTO,
    http_client: AsyncHttpClient = Depends(get_httpx),
):
    """验证 Cloudflare Turnstile 验证码

    接收前端提交的 Turnstile 验证 token，向 Cloudflare API 进行验证。

    Args:
        data: 包含 token 和可选的 remote_ip 的请求数据
        http_client: HTTP 客户端

    Returns:
        TurnstileValidateVO: 验证结果，包含 success、challenge_ts、hostname 等字段

    References:
        https://developers.cloudflare.com/turnstile/get-started/server-side-validation/
    """
    result = await CaptchaService.validate_cloudflare_turnstile(
        token=data.token,
        remote_ip=data.remote_ip,
        http_client=http_client,
    )

    if result.success:
        return ResponseUtil.success(data=TurnstileValidateVO.model_validate(result))
    return ResponseUtil.fail(
        data=TurnstileValidateVO.model_validate(result),
    )
