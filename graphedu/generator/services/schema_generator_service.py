"""Pydantic Schema 生成服务（优化版 - 直接使用 model_json_schema）

本模块提供从 Pydantic 模型类生成 JSON Schema 的功能。

主要功能:
    - 支持通过类路径导入任意 Pydantic 模型
    - 支持快捷方式（如 'service' 自动映射到 ServiceConfig）
    - 直接调用 Pydantic 的 model_json_schema() 方法
    - 将 Schema 导出到文件（默认 .generated 目录）

快捷方式映射:
    service       -> graphedu.common.config.modes.service.ServiceConfig

使用方式:
    from graphedu.generator.services import SchemaGeneratorService

    service = SchemaGeneratorService()
    # 默认输出到 .generated 目录
    schema = service.generate_schema(class_path="service")
    # 指定输出路径
    schema = service.generate_schema(class_path="service", output_path="./schemas/service.json")
"""

import importlib
import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from graphedu.common.utils.strings import pascal_to_snake

logger = logging.getLogger(__name__)


class SchemaGeneratorService:
    """Pydantic Schema 生成服务（优化版）

    职责：
    1. 解析类路径（支持快捷方式）
    2. 动态导入 Pydantic 类
    3. 直接调用 model_json_schema() 生成 JSON Schema
    4. 写入文件或返回字典
    """

    # 快捷方式映射
    SHORTCUTS: dict[str, str] = {
        "service": "graphedu.common.config.modes.service.ServiceConfig",
    }

    def __init__(self, shortcuts: dict[str, str] | None = None):
        """初始化服务

        Args:
            shortcuts: 自定义快捷方式映射（可选）
        """
        if shortcuts is not None:
            self.shortcuts = {**self.SHORTCUTS, **shortcuts}
        else:
            self.shortcuts = self.SHORTCUTS

    def resolve_class_path(self, class_path: str) -> str:
        """解析类路径（支持快捷方式）

        Args:
            class_path: 类路径或快捷方式

        Returns:
            完整的类路径
        """
        if class_path in self.shortcuts:
            resolved = self.shortcuts[class_path]
            logger.info(f"快捷方式 '{class_path}' 解析为 '{resolved}'")
            return resolved
        return class_path

    def import_pydantic_class(self, class_path: str) -> type[BaseModel]:
        """动态导入 Pydantic 类

        Args:
            class_path: 完整的类路径（格式：module.path.ClassName）

        Returns:
            导入的类

        Raises:
            ImportError: 当模块导入失败时
            AttributeError: 当类不存在时
            ValueError: 当类不是 Pydantic 模型时
        """
        # 分割模块路径和类名
        parts = class_path.split(".")
        if len(parts) < 2:
            raise ValueError(f"无效的类路径格式: {class_path}。期望格式: module.path.ClassName")

        *module_parts, class_name = parts
        module_path = ".".join(module_parts)

        try:
            # 动态导入模块
            module = importlib.import_module(module_path)

            # 获取类
            pydantic_class: type[BaseModel] = getattr(module, class_name, None)
            if pydantic_class is None:
                raise AttributeError(f"在模块 {module_path} 中未找到类 {class_name}")

            # 检查是否为 BaseModel 的子类
            if not isinstance(pydantic_class, type) or not issubclass(pydantic_class, BaseModel):
                raise ValueError(f"类 {class_name} 不是 Pydantic BaseModel 的子类。确保该类继承自 pydantic.BaseModel")

            logger.info(f"成功导入类: {class_path}")
            return pydantic_class

        except ImportError as e:
            raise ImportError(f"导入模块失败: {module_path}") from e
        except (AttributeError, ValueError):
            raise
        except Exception as e:
            raise RuntimeError(f"导入类时发生错误: {e}") from e

    def get_default_output_path(self, class_path: str, output_dir: Path) -> Path:
        """获取默认输出路径

        Args:
            class_path: 类路径
            output_dir: 输出目录

        Returns:
            输出文件的完整路径
        """
        class_name = pascal_to_snake(class_path.split(".")[-1])
        return output_dir / f"{class_name.lower()}_schema.json"

    def generate_schema(
        self,
        class_path: str,
        output_path: str | Path | None = None,
        pretty: bool = True,
    ) -> dict[str, Any]:
        """生成 Pydantic 模型的 JSON Schema

        直接使用 Pydantic 的 model_json_schema() 方法，适用于所有 Pydantic v2 模型。

        Args:
            class_path: Pydantic 类路径或快捷方式
            output_path: 输出路径（None 则默认输出到 .generated 目录）
            pretty: 是否格式化 JSON 输出

        Returns:
            生成的 Schema 字典
        """
        # 解析类路径
        resolved_path = self.resolve_class_path(class_path)

        # 导入 Pydantic 类
        pydantic_class = self.import_pydantic_class(resolved_path)

        # 直接调用 model_json_schema() 生成 JSON Schema
        logger.info(f"正在生成 {resolved_path} 的 JSON Schema...")
        try:
            schema = pydantic_class.model_json_schema()
        except Exception as e:
            raise ValueError(f"生成 JSON Schema 失败: {e}") from e

        # 确定输出路径
        if output_path is None:
            # 默认输出到 .generated 目录
            output_dir = Path(".generated")
            output_file = self.get_default_output_path(resolved_path, output_dir)
        else:
            output_path = Path(output_path)
            # 如果是目录或空字符串，使用默认文件名
            if output_path.is_dir() or str(output_path) == "" or output_path.suffix == "":
                output_dir = output_path if output_path.is_dir() else Path(output_path)
                output_file = self.get_default_output_path(resolved_path, output_dir)
            else:
                output_file = output_path

        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 写入 JSON 文件
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                if pretty:
                    json.dump(schema, f, ensure_ascii=False, indent=2)
                else:
                    json.dump(schema, f, ensure_ascii=False)
            logger.info(f"JSON Schema 已生成: {output_file}，包含 {len(schema.get('properties', {}))} 个属性")
        except Exception as e:
            raise ValueError(f"写入文件失败: {e}") from e

        return schema

    def list_shortcuts(self) -> dict[str, str]:
        """列出所有可用的快捷方式

        Returns:
            快捷方式映射字典
        """
        return self.shortcuts.copy()
