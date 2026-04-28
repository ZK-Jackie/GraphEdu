"""验证码服务模块。

该模块提供验证码生成功能，支持算术验证码图片的生成和 Cloudflare Turnstile 验证。
"""

import base64
import json
import logging
import random

from captcha.image import ImageCaptcha

from graphedu.common.config.manager import get_config
from graphedu.common.models.bo import TurnstileValidateResult
from graphedu.common.resource import AsyncHttpClient

logger = logging.getLogger(__name__)


class CaptchaService:
    """验证码服务类。

    提供验证码图片生成功能和 Cloudflare Turnstile 验证功能。
    """

    @staticmethod
    async def create_captcha_image() -> tuple[str, int]:
        """生成算术验证码图片。

        生成一个包含算术表达式（加、减、乘）的验证码图片，
        返回 base64 编码的图片字符串和计算结果。使用了 captcha 库，
        自带干扰线和噪点，能够有效防止 OCR，且内置字体，无需服务器安装字体。

        Returns:
            tuple[str, int]: 包含两个元素的元组：
                - base64 编码的 PNG 图片字符串
                - 算术表达式的计算结果
        """
        # 生成两个1-9之间的随机整数 (避免0乘法或减法出现意外情况)
        num1 = random.randint(1, 9)
        num2 = random.randint(1, 9)

        # 从运算符列表中随机选择一个，乘法用 'x' 以获得更好的展示效果
        operational_character_list = ["+", "-", "x"]
        operational_character = random.choice(operational_character_list)

        # 根据选择的运算符进行计算
        if operational_character == "+":
            result = num1 + num2
        elif operational_character == "-":
            # 确保大数减小数
            if num1 < num2:
                num1, num2 = num2, num1
            result = num1 - num2
        else:
            result = num1 * num2

        # 拼接验证码文本
        text = f"{num1}{operational_character}{num2}=?"

        # 使用 captcha 库生成带有干扰线和噪点的验证码图片，内置字体
        image = ImageCaptcha(width=160, height=60)
        buffer = image.generate(text)

        # 将图像数据转换为base64字符串
        base64_string = base64.b64encode(buffer.getvalue()).decode()

        logger.debug(f"生成验证码: {text}, 结果: {result}")

        return base64_string, result

    @staticmethod
    async def validate_cloudflare_turnstile(
        token: str,
        remote_ip: str | None = None,
        http_client: AsyncHttpClient | None = None,
    ) -> TurnstileValidateResult:
        """验证 Cloudflare Turnstile 验证码

        Args:
            token: 用户端返回的验证 token
            remote_ip: 可选的用户 IP 地址
            http_client: HTTP 客户端，如果为 None 则创建新的客户端

        Returns:
            TurnstileValidateResult: 验证结果，包含 success、challenge_ts、hostname 等字段

        References:
            https://developers.cloudflare.com/turnstile/get-started/server-side-validation/
        """
        config = get_config().security.turnstile
        url = config.verify_url
        secret = config.secret
        timeout = config.timeout

        # 构建请求数据
        data = {"secret": secret, "response": token}
        if remote_ip:
            data["remoteip"] = remote_ip

        # 默认返回值（失败情况）
        default_result = TurnstileValidateResult(
            success=False,
            challenge_ts=None,
            hostname=None,
            error_codes=None,
            action=None,
            cdata=None,
        )

        try:
            status_code = 0
            response_text = ""
            # 使用提供的 HTTP 客户端或直接使用 httpx
            if http_client:
                status_code, response_text = await http_client.post(
                    url,
                    data=data,
                    timeout=timeout,
                )
            else:
                import httpx

                async with httpx.AsyncClient() as client:
                    response = await client.post(url, data=data, timeout=timeout)
                    status_code = response.status_code
                    response_text = response.text

            if status_code == 200:
                result = json.loads(response_text)
                if result.get("success", False):
                    logger.info("Cloudflare Turnstile 验证成功")
                    return TurnstileValidateResult(
                        success=True,
                        challenge_ts=result.get("challenge_ts"),
                        hostname=result.get("hostname"),
                        error_codes=None,
                        action=result.get("action"),
                        cdata=result.get("cdata"),
                    )

                error_codes = result.get("error-codes", [])
                logger.warning(f"Cloudflare Turnstile 验证失败: {error_codes}")
                default_result.error_codes = error_codes
                return default_result

            logger.warning(f"Cloudflare Turnstile API 返回错误状态码: {status_code}")
            default_result.error_codes = ["invalid-response"]
            return default_result

        except Exception as e:
            logger.error(f"Cloudflare Turnstile 验证请求异常: {e}")
            default_result.error_codes = ["internal-error"]
            return default_result
