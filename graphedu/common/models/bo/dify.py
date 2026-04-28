"""Dify 相关 BO 模块

定义了 Dify workflow API 响应的业务对象模型
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class DifyFile(BaseModel):
    """Dify 文件上传对象"""

    type: Literal["document", "image", "audio", "video", "custom"] = Field(description="上传的文件类型")
    transfer_method: Literal["remote_url", "local_file"] = Field(
        description="传递方式，remote_url 图片地址 / local_file 上传文件"
    )
    url: str | None = Field(default=None, description="文件URL，transfer_method 为 remote_url 时必填")
    upload_file_id: str | None = Field(
        default=None, description="上传文件ID，transfer_method 为 local_file 时必填，通过文件上传接口响应可以获得"
    )


class DifyWorkflowFileInfo(BaseModel):
    """Dify workflow 文件信息模型"""

    id: str | None = Field(default=None, description="文件ID")
    name: str | None = Field(default=None, description="文件名称")
    size: int | None = Field(default=None, description="文件大小")
    type: str | None = Field(default=None, description="文件类型")
    url: str | None = Field(default=None, description="文件URL")


class DifyWorkflowCreatedBy(BaseModel):
    """Dify workflow 创建者信息模型"""

    id: str | None = Field(default=None, description="创建者ID")
    name: str | None = Field(default=None, description="创建者名称")
    email: str | None = Field(default=None, description="创建者邮箱")


class DifyWorkflowRunData(BaseModel):
    """Dify workflow 运行数据模型

    Attributes:
        id: 运行 ID
        workflow_id: workflow ID
        status: 运行状态
        outputs: workflow 输出结果
        error: 错误信息
        elapsed_time: 耗时（秒）
        total_tokens: 总 token 数
        total_steps: 总步骤数
        created_at: 创建时间戳
        finished_at: 完成时间戳
        created_by: 创建者信息
        exceptions_count: 异常数量
        files: 文件列表
    """

    id: str | None = Field(default=None, description="运行ID")
    workflow_id: str | None = Field(default=None, description="workflow ID")
    status: str | None = Field(default=None, description="运行状态")
    outputs: dict[str, Any] | None = Field(default=None, description="workflow 输出结果")
    error: str | None = Field(default=None, description="错误信息")
    elapsed_time: float | None = Field(default=None, description="耗时（秒）")
    total_tokens: int | None = Field(default=None, description="总 token 数")
    total_steps: int | None = Field(default=None, description="总步骤数")
    created_at: int | None = Field(default=None, description="创建时间戳")
    finished_at: int | None = Field(default=None, description="完成时间戳")
    created_by: DifyWorkflowCreatedBy | None = Field(default=None, description="创建者信息")
    exceptions_count: int | None = Field(default=None, description="异常数量")
    files: list[DifyWorkflowFileInfo] | None = Field(default=None, description="文件列表")


class DifyWorkflowResponse(BaseModel):
    """Dify workflow API 响应模型

    Attributes:
        task_id: 任务 ID
        workflow_run_id: workflow 运行 ID
        data: workflow 运行数据
    """

    task_id: str | None = Field(default=None, description="任务 ID")
    workflow_run_id: str | None = Field(default=None, description="workflow 运行 ID")
    data: DifyWorkflowRunData | None = Field(default=None, description="workflow 运行数据")
