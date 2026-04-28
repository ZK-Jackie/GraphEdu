"""安全切面模块

本模块提供安全相关的切面功能，通过依赖注入和装饰器实现横切关注点。

核心功能：
- 数据权限控制：基于角色的数据范围限制（全部/自定义/本部门/本部门及以下/仅本人）
- 接口权限校验：基于权限标识和角色的接口访问控制
- 日志记录：自动记录系统登录日志和操作日志

主要组件：
- GetDataScope: 数据权限依赖注入类，用于在数据查询时自动应用数据权限过滤
- CheckUserInterfacePermit: 接口权限校验类，基于权限标识验证用户访问权限
- CheckRoleInterfaceAuth: 接口权限校验类，基于角色验证用户访问权限
- SystemLog: 日志装饰器，自动记录方法调用的详细日志信息

使用方式：
```python
# 数据权限控制
@router.get("/users")
async def get_users(
    data_scope: GetDataScope = Depends(),
    db: AsyncSession = Depends(get_db)
):
    where_clause = data_scope()
    result = await db.execute(select(User).where(text(where_clause)))

# 接口权限校验
@router.post("/user/add")
async def add_user(
    _: None = Depends(CheckUserInterfacePermit("system:user:add"))
):
    pass

# 日志记录
@SystemLog(title="用户管理", business_type=BusinessType.INSERT)
async def create_user(request: Request, ...):
    pass
```
"""

from .data_scope import GetDataScope
from .interface_auth import CheckRoleInterfaceAuth, CheckUserInterfacePermit
from .log_annotation import SystemLog

__all__ = [
    "CheckRoleInterfaceAuth",
    "CheckUserInterfacePermit",
    "GetDataScope",
    "SystemLog",
]
