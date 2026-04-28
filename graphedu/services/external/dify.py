"""Dify 接口调用"""

import json
import logging
from typing import TypeVar, overload

from pydantic import BaseModel

from graphedu.common.models.bo.dify import DifyWorkflowResponse
from graphedu.common.resource import AsyncHttpClient

logger = logging.getLogger(__name__)

DifyReturnDataModel = TypeVar("DifyReturnDataModel", bound=BaseModel)


class DifyService:
    """Diff Service"""

    @overload
    @staticmethod
    async def invoke_workflow(
        inputs: dict | BaseModel,
        user: str,
        api_key: str,
        base_url: str,
        http_client: AsyncHttpClient,
        workflow_id: str | None = ...,
        return_model: type[DifyReturnDataModel] = ...,
    ) -> DifyReturnDataModel: ...
    @overload
    @staticmethod
    async def invoke_workflow(
        inputs: dict | BaseModel,
        user: str,
        api_key: str,
        base_url: str,
        http_client: AsyncHttpClient,
        workflow_id: str | None = ...,
        return_model: None = ...,
    ) -> DifyWorkflowResponse: ...
    @staticmethod
    async def invoke_workflow(
        inputs: dict | BaseModel,
        user: str,
        api_key: str,
        base_url: str,
        http_client: AsyncHttpClient,
        workflow_id: str | None = None,
        return_model: type[DifyReturnDataModel] | None = None,
    ) -> DifyWorkflowResponse | DifyReturnDataModel | None:
        """调用 dify 工作流

        Args:
            inputs: workflow 输入参数，可以是 dict 或 BaseModel
            user: 用户标识
            api_key: 该 Workflow 的 API 密钥
            base_url: Dify API 基础 URL
            http_client: 异步 HTTP 客户端
            workflow_id: workflow ID，为空时调用 /workflows/run（最新版本）
            return_model: 可选，如果提供则将 data.outputs 转换为该模型类型返回

        Returns:
            如果提供 return_model，返回对应的模型实例；否则返回 DifyWorkflowResponse

        Raises:
            HTTPClientException: HTTP 客户端未初始化
            HTTPTimeoutException: 请求超时
            HTTPConnectionException: 连接失败
            HTTPRequestException: 请求失败
        """
        # 构建 URL：有 id 用 /workflows/{id}/run，无 id 用 /workflows/run（id 可能为 None 或空字符串）
        base = base_url.rstrip("/")
        url = f"{base}/workflows/{workflow_id}/run" if workflow_id else f"{base}/workflows/run"

        # 准备请求头
        headers = {
            "Authorization": f"{api_key if api_key.startswith('Bearer') else 'Bearer ' + api_key}",
            "Content-Type": "application/json",
        }

        # 准备请求体
        if isinstance(inputs, BaseModel):
            inputs_dict = inputs.model_dump(by_alias=True, exclude_none=True)
        else:
            inputs_dict = inputs

        request_body = {
            "inputs": inputs_dict,
            "response_mode": "blocking",
            "user": user,
        }

        # 发送请求
        logger.debug(f"调用 Dify workflow: {url}, user={user}, workflow_id={workflow_id or '(latest)'}")
        status_code, response_text = await http_client.post(url, data=request_body, headers=headers)

        # 解析响应
        if status_code != 200:
            logger.warning(f"Dify workflow 返回非 200 状态码: {status_code}, response={response_text}")
        response = DifyWorkflowResponse.model_validate_json(response_text)

        # 根据 return_model 参数决定返回类型
        if return_model is not None and response.data and response.data.outputs is not None:
            return return_model.model_validate(response.data.outputs)

        return response.data.outputs if response.data else None

    @overload
    @staticmethod
    async def invoke_workflow_streaming(
        inputs: dict | BaseModel,
        user: str,
        api_key: str,
        base_url: str,
        http_client: AsyncHttpClient,
        workflow_id: str | None = ...,
        return_model: type[DifyReturnDataModel] = ...,
        timeout: float = ...,
    ) -> DifyReturnDataModel: ...

    @overload
    @staticmethod
    async def invoke_workflow_streaming(
        inputs: dict | BaseModel,
        user: str,
        api_key: str,
        base_url: str,
        http_client: AsyncHttpClient,
        workflow_id: str | None = ...,
        return_model: None = ...,
        timeout: float = ...,
    ) -> DifyWorkflowResponse: ...

    @staticmethod
    async def invoke_workflow_streaming(
        inputs: dict | BaseModel,
        user: str,
        api_key: str,
        base_url: str,
        http_client: AsyncHttpClient,
        workflow_id: str | None = None,
        return_model: type[DifyReturnDataModel] | None = None,
        timeout: float = 300.0,
    ) -> DifyWorkflowResponse | DifyReturnDataModel | None:
        """调用 Dify 工作流（流式模式），通过 SSE 逐步接收事件，避免长时间阻塞导致超时。

        与 ``invoke_workflow`` 参数和返回值完全一致，区别在于内部使用
        ``response_mode: "streaming"``，通过逐行解析 SSE 事件来保持连接活跃，
        从而绕过各层代理（Nginx 等）的 read timeout 限制。

        Args:
            inputs: workflow 输入参数，可以是 dict 或 BaseModel
            user: 用户标识
            api_key: 该 Workflow 的 API 密钥
            base_url: Dify API 基础 URL
            http_client: 异步 HTTP 客户端
            workflow_id: workflow ID，为空时调用 /workflows/run（最新版本）
            return_model: 可选，如果提供则将 data.outputs 转换为该模型类型返回
            timeout: 单次读取超时（秒），默认 300s。注意这是每个 SSE 事件之间的等待时间，
                     而非整个工作流的最大执行时间，因此不需要设得很大。

        Returns:
            如果提供 return_model，返回对应的模型实例；否则返回 DifyWorkflowResponse

        Raises:
            HTTPClientException: HTTP 客户端未初始化
            HTTPTimeoutException: 请求超时
            HTTPConnectionException: 连接失败
            HTTPRequestException: 请求失败
        """
        base = base_url.rstrip("/")
        url = f"{base}/workflows/{workflow_id}/run" if workflow_id else f"{base}/workflows/run"

        headers = {
            "Authorization": f"{api_key if api_key.startswith('Bearer') else 'Bearer ' + api_key}",
            "Content-Type": "application/json",
        }

        if isinstance(inputs, BaseModel):
            inputs_dict = inputs.model_dump(by_alias=True, exclude_none=True)
        else:
            inputs_dict = inputs

        request_body = {
            "inputs": inputs_dict,
            "response_mode": "streaming",
            "user": user,
        }

        logger.debug(f"调用 Dify workflow (streaming): {url}, user={user}, workflow_id={workflow_id or '(latest)'}")

        # 逐行解析 SSE，等待 workflow_finished 事件
        current_event: str | None = None
        result: DifyWorkflowResponse | DifyReturnDataModel | None = None

        async for line in http_client.stream_post(url, data=request_body, headers=headers, timeout=timeout):
            line = line.strip()
            if not line:
                # 空行是 SSE 事件分隔符
                current_event = None
                continue

            if line.startswith("event: "):
                current_event = line[7:].strip()
                continue

            if line.startswith("data: "):
                payload = line[6:]
                try:
                    event_data = json.loads(payload)
                except json.JSONDecodeError:
                    logger.warning(f"无法解析 SSE data: {payload[:200]}")
                    continue

                # Dify 把 event 类型放在 JSON 的 "event" 字段中，也可能在 SSE event: 行
                event_type = event_data.get("event") or current_event

                if event_type == "workflow_finished":
                    # data 字段结构与 blocking 模式下的完整响应一致
                    response = DifyWorkflowResponse.model_validate(event_data)
                    if return_model is not None and response.data and response.data.outputs is not None:
                        result = return_model.model_validate(response.data.outputs)
                    else:
                        result = response.data.outputs if response.data else None

                elif event_type == "error":
                    logger.error(
                        f"Dify workflow streaming 错误: workflow_id={workflow_id or '(latest)'}, error={event_data}"
                    )

                continue

        return result
