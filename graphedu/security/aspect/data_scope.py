"""数据权限控制模块

本模块提供基于角色的数据权限控制功能，用于限制用户可以访问的数据范围。

核心类：
- GetDataScope: 数据权限依赖注入类，根据用户角色生成 SQL WHERE 条件

数据权限范围：
- DATA_SCOPE_ALL (1): 全部数据权限
- DATA_SCOPE_CUSTOM (2): 自定义数据权限（通过 sys_role_dept 配置）
- DATA_SCOPE_DEPT (3): 本部门数据权限
- DATA_SCOPE_DEPT_AND_CHILD (4): 本部门及以下数据权限
- DATA_SCOPE_SELF (5): 仅本人数据权限

使用方式：
```python
from fastapi import Depends
from sqlalchemy import select, text

@router.get("/users")
async def get_users(
    data_scope: GetDataScope = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # 获取数据权限的 WHERE 条件
    where_clause = data_scope()
    # 在查询中应用权限过滤
    result = await db.execute(
        select(User).where(text(where_clause))
    )
    return result.scalars().all()
```

注意事项：
- 管理员用户（role_id=1）自动拥有全部数据权限
- 当前版本为简化实现，部分高级数据权限功能（如自定义部门范围、子部门查询）待完善
- 当用户无角色时，默认只能查看自己的数据
"""

from fastapi import Depends

from graphedu.common.models.bo import CurrentUser
from graphedu.security.auth import SecurityService


class GetDataScope:
    """获取当前用户数据权限对应的查询 SQL 语句

    根据用户角色生成数据权限过滤的 SQL WHERE 条件。

    注意：当前版本为简化实现，部分高级数据权限功能待完善。

    Attributes:
        DATA_SCOPE_ALL: 全部数据权限
        DATA_SCOPE_CUSTOM: 自定义数据权限
        DATA_SCOPE_DEPT: 本部门数据权限
        DATA_SCOPE_DEPT_AND_CHILD: 本部门及以下数据权限
        DATA_SCOPE_SELF: 仅本人数据权限
    """

    DATA_SCOPE_ALL = "1"
    DATA_SCOPE_CUSTOM = "2"
    DATA_SCOPE_DEPT = "3"
    DATA_SCOPE_DEPT_AND_CHILD = "4"
    DATA_SCOPE_SELF = "5"

    def __init__(
        self,
        query_alias: str | None = "",
        db_alias: str | None = "db",
        user_alias: str | None = "user_id",
        dept_alias: str | None = "dept_id",
    ):
        """初始化数据权限生成器

        Args:
            query_alias: 所要查询表对应的 SQLAlchemy 模型名称，默认为 ''
            db_alias: ORM 对象别名，默认为 'db'
            user_alias: 用户 ID 字段别名，默认为 'user_id'
            dept_alias: 部门 ID 字段别名，默认为 'dept_id'
        """
        self.query_alias = query_alias
        self.db_alias = db_alias
        self.user_alias = user_alias
        self.dept_alias = dept_alias

    def __call__(self, current_user: CurrentUser = Depends(SecurityService.get_current_user)):
        """根据当前用户的角色数据权限，生成对应的 SQL WHERE 条件

        数据范围说明：
        1 - 全部数据权限
        2 - 自定义数据权限（通过 sys_role_dept 配置）
        3 - 本部门数据权限
        4 - 本部门及以下数据权限
        5 - 仅本人数据权限

        Args:
            current_user: 当前用户信息对象

        Returns:
            str: SQL WHERE 条件表达式
        """
        # 管理员有全部数据权限
        if current_user.is_admin():
            return "True"

        # 如果用户没有角色，只能查看自己的数据
        if not current_user.detail or not hasattr(current_user.detail, "roles") or not current_user.detail.roles:
            if self.query_alias == "SysUser":
                return f"{self.user_alias} = {current_user.detail.user.user_id if current_user.detail.user else 0}"
            return "False"  # 其他表无权访问

        # 获取用户所有角色的最大数据权限范围
        data_scopes = []
        for role in current_user.detail.roles:
            if hasattr(role, "data_scope"):
                data_scopes.append(role.data_scope)

        if not data_scopes:
            # 没有数据权限配置，默认只能查看自己的
            if self.query_alias == "SysUser":
                return f"{self.user_alias} = {current_user.detail.user.user_id}"
            return "False"

        # 如果有任一角色是全部数据权限
        if self.DATA_SCOPE_ALL in data_scopes:
            return "True"

        sql_parts = []
        user_dept_ids = (
            [dept.dept_id for dept in current_user.detail.depts] if hasattr(current_user.detail, "depts") else []
        )

        # 处理各种数据权限范围
        for scope in set(data_scopes):
            if scope == self.DATA_SCOPE_CUSTOM:  # 自定数据权限（通过sys_role_dept配置）
                # TODO: 需要查询sys_role_dept表获取自定义部门范围
                # 这里暂时简化为本部门
                if user_dept_ids and self.dept_alias:
                    sql_parts.append(f"{self.dept_alias} IN ({','.join(map(str, user_dept_ids))})")
            elif scope == self.DATA_SCOPE_DEPT:  # 本部门数据权限
                if user_dept_ids and self.dept_alias:
                    sql_parts.append(f"{self.dept_alias} IN ({','.join(map(str, user_dept_ids))})")
            elif scope == self.DATA_SCOPE_DEPT_AND_CHILD:  # 本部门及以下数据权限  # noqa: SIM102
                if user_dept_ids and self.dept_alias:
                    # TODO: 需要查询部门树获取子部门
                    # 这里暂时简化为本部门
                    sql_parts.append(f"{self.dept_alias} IN ({','.join(map(str, user_dept_ids))})")

        # 如果是SysUser表，还要包含用户自己的数据
        if self.query_alias == "SysUser" and current_user.detail and current_user.detail.user:
            sql_parts.append(f"{self.user_alias} = {current_user.detail.user.user_id}")

        if not sql_parts:
            return "False"

        return " OR ".join(sql_parts)
