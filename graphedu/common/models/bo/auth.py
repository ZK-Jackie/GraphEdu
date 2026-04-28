"""认证相关 DTO 模块

本模块定义了用户认证相关的数据传输对象，包括：

- **AccessTokenPayload**: JWT Token 载荷结构
"""

from typing import TypedDict


class AccessTokenPayload(TypedDict):
    """访问令牌载荷结构

    定义 JWT Token 中包含的用户信息字段

    Attributes:
        user_id: 用户 ID
        user_name: 用户名
        dept_names: 部门名称列表
        session_id: 会话 ID
        login_info: 登录信息字典
    """

    user_id: int
    user_name: str
    dept_names: list[str]
    session_id: str
    login_info: dict
