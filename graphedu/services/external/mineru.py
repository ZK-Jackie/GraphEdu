"""MinerU API 服务

负责调用 MinerU API 进行 PDF 解析，支持任务提交和状态轮询。
"""

from dataclasses import dataclass
import logging

import httpx

from graphedu.common.config.manager import get_config

logger = logging.getLogger(__name__)


@dataclass
class MinerUTaskResponse:
    """MinerU 任务响应"""

    task_id: str
    status: str
    message: str | None = None
    result: dict | None = None


class MineruService:
    """MinerU API 服务类"""

    @staticmethod
    async def submit_parse_task(pdf_url: str, title: str | None = None) -> MinerUTaskResponse:
        """提交 PDF 解析任务"""
        config = get_config()
        endpoint = f"{config.mineru.base_url}/api/v1/parse"
        payload = {"pdf_url": pdf_url, "title": title}

        headers = {}
        if config.mineru.api_key:
            headers["Authorization"] = f"Bearer {config.mineru.api_key}"

        async with httpx.AsyncClient(timeout=config.mineru.timeout) as client:
            try:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                return MinerUTaskResponse(
                    task_id=data["task_id"],
                    status=data.get("status", "submitted"),
                    message=data.get("message"),
                )
            except httpx.HTTPError as e:
                logger.error(f"MinerU API 调用失败: {e}")
                from graphedu.common.exceptions.services.education.external import (
                    MinerUApiException,
                )

                raise MinerUApiException(message=f"提交解析任务失败: {e!s}") from e

    @staticmethod
    async def get_task_status(task_id: str) -> MinerUTaskResponse:
        """获取任务状态"""
        config = get_config()
        endpoint = f"{config.mineru.base_url}/api/v1/tasks/{task_id}"

        headers = {}
        if config.mineru.api_key:
            headers["Authorization"] = f"Bearer {config.mineru.api_key}"

        async with httpx.AsyncClient(timeout=config.mineru.timeout) as client:
            try:
                response = await client.get(endpoint, headers=headers)
                response.raise_for_status()
                data = response.json()

                return MinerUTaskResponse(
                    task_id=task_id,
                    status=data["status"],
                    message=data.get("message"),
                    result=data.get("result"),
                )
            except httpx.HTTPError as e:
                logger.error(f"获取 MinerU 任务状态失败: {e}")
                from graphedu.common.exceptions.services.education.external import (
                    MinerUApiException,
                )

                raise MinerUApiException(message=f"获取任务状态失败: {e!s}") from e

    @staticmethod
    async def download_result(result_url: str) -> list[str]:
        r"""下载解析结果（按页返回 Markdown 内容）

        Args:
            result_url: 结果文件 URL（由 get_task_status 返回的 result.result_url）

        Returns:
            list[str]: 按页返回的 Markdown 内容列表，如 ["# Page 1\n...", "# Page 2\n..."]

        Raises:
            MinerUApiException: 下载失败时抛出
        """
        config = get_config()
        headers = {}
        if config.mineru.api_key:
            headers["Authorization"] = f"Bearer {config.mineru.api_key}"

        async with httpx.AsyncClient(timeout=config.mineru.timeout) as client:
            try:
                response = await client.get(result_url, headers=headers)
                response.raise_for_status()
                data = response.json()

                # MinerU 返回格式：{"pages": [{"page": 1, "markdown": "..."}, ...]}
                # 或直接返回 {"markdown": "全文内容"} 取决于具体版本
                if "pages" in data:
                    return [page.get("markdown", "") for page in data["pages"]]
                if "markdown" in data:
                    return [data["markdown"]]
                logger.warning(f"MinerU 结果格式未知: {list(data.keys())}")
                return []
            except httpx.HTTPError as e:
                logger.error(f"下载 MinerU 解析结果失败: {e}")
                from graphedu.common.exceptions.services.education.external import (
                    MinerUApiException,
                )

                raise MinerUApiException(message=f"下载解析结果失败: {e!s}") from e
