"""Generator 服务层模块

本模块包含按场景划分的各种代码生成服务。

服务类型:
    - CodeGeneratorService: 代码生成服务（表管理、代码预览、批量生成）
    - EnvGeneratorService: 环境变量生成服务
    - SchemaGeneratorService: Pydantic Schema 生成服务
    - generate_model: CLI 直接从 DB 生成 ORM 模型
    - generate_crud:  CLI 直接从 DB 生成完整 CRUD

使用方式:
    from graphedu.generator.services import CodeGeneratorService
    from graphedu.generator.services import EnvGeneratorService
    from graphedu.generator.services import SchemaGeneratorService
    from graphedu.generator.services import generate_model, generate_crud
"""

from graphedu.generator.services.cli_generator import generate_crud, generate_model
from graphedu.generator.services.env_generator_service import EnvGeneratorService
from graphedu.generator.services.schema_generator_service import SchemaGeneratorService
from graphedu.services.generator.code_generator import CodeGeneratorService

__all__ = [
    "CodeGeneratorService",
    "EnvGeneratorService",
    "SchemaGeneratorService",
    "generate_crud",
    "generate_model",
]
