"""GraphEdu 通用数据模型模块

本模块定义了系统中使用的所有数据模型，包括：

## 模型分层架构

### DTO (Data Transfer Objects) - 数据传输对象
用于 API 请求参数验证，定义输入数据结构和验证规则

### VO (View Objects) - 视图对象
用于 API 响应数据，配置序列化规则，支持从 ORM 对象创建

### PO (Persistent Objects) - 持久化对象
用于数据库操作的业务模型，支持 Create/Update/Query 变体

### ORM - SQLAlchemy ORM 模型
用于数据库表映射，供数据访问层使用

### Constants - 系统常量
定义系统运行所需的各种常量

## 使用场景

### API 层（Controller）
```python
from graphedu.common.models.dto import UserQueryDTO
from graphedu.common.models.vo import UserListVO
from fastapi import APIRouter

router = APIRouter()

@router.get("/users", response_model=UserListVO)
async def list_users(query: UserQueryDTO):
    ...
```

### 服务层
```python
from graphedu.common.models.po import CurrentUser
from graphedu.common.models.orm import SysUser
from graphedu.common.models.vo import UserDetailVO

def get_user_detail(user_id: int) -> UserDetailVO:
    # 使用 ORM 查询数据库
    orm_user = SysUser.get(user_id)
    # 转换为 PO 对象进行业务处理
    po_user = CurrentUser.from_orm(orm_user)
    # 返回 VO 对象
    return UserDetailVO.from_po(po_user)
```

### 数据访问层
```python
from graphedu.common.models.orm import SysUser
from sqlalchemy import select

def get_user_by_id(user_id: int):
    stmt = select(SysUser).where(SysUser.id == user_id)
    return stmt
```
"""

# ============================================================================
# 常量模块
# ============================================================================
from .constants import (
    CommonConstants,
    RedisConstants,
    SystemConstants,
    project_prefix,
)

__all__ = [
    # 常量
    "CommonConstants",
    "RedisConstants",
    "SystemConstants",
    "project_prefix",
]
