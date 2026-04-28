"""VO (View Objects) - 视图对象模块

职责：
1. 定义 API 响应的数据结构
2. 配置序列化规则（from_attributes=True 支持从 ORM 对象创建）
"""

# 基础 VO 类
from graphedu.common.models.vo.base import VO, BatchDeleteResponse, DeleteResultItem

# 通用相关 VO
from graphedu.common.models.vo.commonv2.captcha import TurnstileValidateVO
from graphedu.common.models.vo.educationv2.knowledge_graph import (
    GraphRelationshipCreatedVO,
    GraphRelationshipDetailVO,
    KnowledgeExtractionResultVO,
    KnowledgeGraphDetailVO,
    KnowledgeGraphListVO,
    KnowledgePointDraftVO,
    KnowledgePointVO,
    KnowledgeRelationshipDraftVO,
    NvlGraphDataVO,
    NvlNodeVO,
    NvlRelationshipVO,
)

# 部门相关 VO
from graphedu.common.models.vo.systemv2.dept import (
    DeptDetailVO,
    DeptInfoVO,
    DeptSimpleVO,
    DeptTreeVO,
)

# 字典相关 VO
from graphedu.common.models.vo.systemv2.dict import (
    DictDataDetailVO,
    DictDataListVO,
    DictDataSimpleVO,
    DictTypeDetailVO,
    DictTypeListVO,
)

# 功能权限相关 VO
from graphedu.common.models.vo.systemv2.function import (
    FunctionDetailVO,
    FunctionListVO,
    FunctionTreeVO,
)

# 日志相关 VO
from graphedu.common.models.vo.systemv2.log import (
    LoginLogDetailVO,
    LoginLogListVO,
    OperLogDetailVO,
    OperLogListVO,
)

# 角色相关 VO
from graphedu.common.models.vo.systemv2.role import (
    RoleDetailVO,
    RoleListVO,
    RoleSimpleVO,
)

# 用户相关 VO
from graphedu.common.models.vo.systemv2.user import (
    UserDetailVO,
    UserInfoVO,
    UserListVO,
    UserProfileVO,
    UserRoleListVO,
    UserRoleVO,
)

# 代码生成器相关 VO
from graphedu.common.models.vo.toolv2.generator import (
    GenCodePreviewVO,
    GenTableColumnVO,
    GenTableDetailVO,
    GenTableEditInfoVO,
    GenTableInfoVO,
    GenTableListVO,
)

__all__ = [
    "VO",
    "BatchDeleteResponse",
    "DeleteResultItem",
    "DeptDetailVO",
    "DeptInfoVO",
    "DeptSimpleVO",
    "DeptTreeVO",
    "DictDataDetailVO",
    "DictDataListVO",
    "DictDataSimpleVO",
    "DictTypeDetailVO",
    "DictTypeListVO",
    "FunctionDetailVO",
    "FunctionListVO",
    "FunctionTreeVO",
    "GenCodePreviewVO",
    "GenTableColumnVO",
    "GenTableDetailVO",
    "GenTableEditInfoVO",
    "GenTableInfoVO",
    "GenTableListVO",
    "GraphRelationshipCreatedVO",
    "GraphRelationshipDetailVO",
    "KnowledgeExtractionResultVO",
    "KnowledgeGraphDetailVO",
    "KnowledgeGraphListVO",
    "KnowledgePointDraftVO",
    "KnowledgePointVO",
    "KnowledgeRelationshipDraftVO",
    "LoginLogDetailVO",
    "LoginLogListVO",
    "NvlGraphDataVO",
    "NvlNodeVO",
    "NvlRelationshipVO",
    "OperLogDetailVO",
    "OperLogListVO",
    "RoleDetailVO",
    "RoleListVO",
    "RoleSimpleVO",
    "TurnstileValidateVO",
    "UserDetailVO",
    "UserInfoVO",
    "UserListVO",
    "UserProfileVO",
    "UserRoleListVO",
    "UserRoleVO",
]
