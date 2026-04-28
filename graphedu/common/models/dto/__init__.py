"""DTO (Data Transfer Object) 模块

本模块定义了所有数据传输对象，用于 API 请求参数验证

主要子模块：
- **base**: DTO 基类和响应工具
- **auth**: 认证相关 DTO
- **common**: 通用 DTO
- **paginate**: 分页相关 DTO
- **user**: 用户管理 DTO
- **role**: 角色管理 DTO
- **dept**: 部门管理 DTO
- **function**: 功能权限 DTO
- **dict**: 字典管理 DTO
- **log**: 日志管理 DTO
- **upload**: 文件上传 DTO
"""

from graphedu.common.models.dto.educationv2.knowledge_graph import (
    KnowledgeExtractionRequestDTO,
    KnowledgeGraphCreateDTO,
    KnowledgeGraphQueryDTO,
    KnowledgeGraphUpdateDTO,
    KnowledgePointCreateDTO,
    KnowledgePointSaveDTO,
    KnowledgePointUpdateDTO,
    KnowledgeRelationshipCreateDTO,
    KnowledgeRelationshipSaveDTO,
    KnowledgeRelationshipUpdateDTO,
    SaveExtractionRequestDTO,
)
from graphedu.common.models.dto.toolv2.generator import (
    GenDbTableQueryDTO,
    GenTableColumnUpdateDTO,
    GenTableCreateDTO,
    GenTableDeleteDTO,
    GenTableImportDTO,
    GenTableParamsDTO,
    GenTableQueryDTO,
    GenTableUpdateDTO,
)

__all__ = [
    "GenDbTableQueryDTO",
    "GenTableColumnUpdateDTO",
    "GenTableCreateDTO",
    "GenTableDeleteDTO",
    "GenTableImportDTO",
    "GenTableParamsDTO",
    "GenTableQueryDTO",
    "GenTableUpdateDTO",
    "KnowledgeExtractionRequestDTO",
    "KnowledgeGraphCreateDTO",
    "KnowledgeGraphQueryDTO",
    "KnowledgeGraphUpdateDTO",
    "KnowledgePointCreateDTO",
    "KnowledgePointSaveDTO",
    "KnowledgePointUpdateDTO",
    "KnowledgeRelationshipCreateDTO",
    "KnowledgeRelationshipSaveDTO",
    "KnowledgeRelationshipUpdateDTO",
    "SaveExtractionRequestDTO",
]
