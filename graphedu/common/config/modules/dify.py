"""Dify 配置模块"""

from pydantic import BaseModel, Field


class WorkflowConfig(BaseModel):
    """单个 Workflow 配置"""

    id: str | None = Field(default=None, description="Workflow ID，为空时调用最新版本")
    api_key: str = Field(default="", description="该 Workflow 的 API 密钥")


class DifyWorkflowsConfig(BaseModel):
    """Dify Workflows 配置"""

    exercise_generation: WorkflowConfig = Field(default_factory=WorkflowConfig, description="习题生成 workflow 配置")
    teacher_exercise_generation: WorkflowConfig = Field(
        default_factory=WorkflowConfig, description="教师端习题生成 workflow 配置"
    )


class DifyConfig(BaseModel):
    """Dify 配置"""

    base_url: str = Field(default="https://api.dify.ai/v1", description="Dify API 基础 URL")
    workflows: DifyWorkflowsConfig = Field(default_factory=DifyWorkflowsConfig, description="Dify Workflows 配置")
