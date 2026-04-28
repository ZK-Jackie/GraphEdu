"""使用 pydantic-settings 的基础配置类。"""

import os
from typing import Any

from pydantic import Field
from pydantic_core import PydanticUndefined
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

from graphedu.common.utils import read_yaml

from .constants import CONFIG_PREFIX, ConfigConstants


class YamlSettingsSource(PydanticBaseSettingsSource):
    """YAML 文件配置源。"""

    def __init__(self, settings_cls: type[BaseSettings]):
        super().__init__(settings_cls)
        self._yaml_data: dict[str, Any] = {}

    def _load_yaml_files(self) -> dict[str, Any]:
        """加载所有 YAML 文件。"""
        yaml_data: dict[str, Any] = {}

        # 1. 读取本地配置文件（GE_CONFIG_FILE_LOCAL）
        local_file = os.environ.get(ConfigConstants.CONFIG_FILE_LOCAL)
        if local_file:
            local_config = read_yaml(local_file, not_found_err=False)
            if isinstance(local_config, dict):
                yaml_data.update(local_config)

        # 2. 读取环境配置文件（GE_CONFIG_FILE_ENV）
        env_file = os.environ.get(ConfigConstants.CONFIG_FILE_ENV)
        if env_file:
            env_config = read_yaml(env_file, not_found_err=False)
            if isinstance(env_config, dict):
                yaml_data.update(env_config)

        return yaml_data

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        """获取字段值（从 YAML 文件）。"""
        # 不直接使用，由 __call__ 统一处理
        return PydanticUndefined, field_name, False

    def __call__(self) -> dict[str, Any]:
        """加载 YAML 配置。"""
        return self._load_yaml_files()


class BaseAppSettings(BaseSettings):
    """应用程序设置基类。

    配置加载优先级（从高到低）：
    1. 初始化值
    2. 环境变量（GRAPHEDU_前缀）
    3. 环境配置文件（GE_CONFIG_FILE_ENV 指定）
    4. 本地配置文件（GE_CONFIG_FILE_LOCAL 指定，默认 dev.config.yaml）
    5. 默认值

    注意：只有顶层配置类（如 ServiceConfig）需要继承此类。
    嵌套配置类应使用 BaseConfigModel。
    """

    description: str | None = Field(default=None)
    """配置描述（仅用于文档，不影响逻辑）"""

    model_config = SettingsConfigDict(
        env_prefix=CONFIG_PREFIX + "_",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",
        arbitrary_types_allowed=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """自定义配置源顺序。"""
        return (
            init_settings,  # 初始化值
            env_settings,  # 环境变量
            YamlSettingsSource(settings_cls),  # YAML 文件
        )
