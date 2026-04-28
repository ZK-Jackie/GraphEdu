"""认证相关视图对象模块。"""

from typing import Literal

from pydantic import Field

from graphedu.common.models.vo.base import VO


class RouterMeta(VO):
    """路由元信息（对应 Vue Router 的 meta 字段）"""

    key: str = Field(description="权限标识（唯一标识）")
    title: str = Field(description="页面标题")
    icon: str | None = Field(default=None, description="菜单图标")
    keep_alive: bool | None = Field(default=None, description="是否缓存页面（对应 route_cache）")
    affix: bool | None = Field(default=None, description="是否固定在标签栏")
    link: str | None = Field(default=None, description="外链地址（当 route_external=1 时有效）")
    hidden: bool | None = Field(default=None, description="是否隐藏（对应 visible=0）")
    enabled: bool | None = Field(default=True, description="是否启用（对应 status=0）")
    order: int | None = Field(default=None, description="显示顺序（对应 sort_order）")
    style: dict | None = Field(default=None, description="菜单CSS样式（JSON格式，使用css-in-js格式）")
    option_style: dict | None = Field(default=None, description="菜单选项样式（JSON格式）")


class RouterVO(VO):
    """路由信息 VO（对齐 Vue Router 的 RouteRecordRaw）"""

    # 基础路由信息
    path: str = Field(description="路由路径")
    name: str | None = Field(default=None, description="路由名称")
    component: str | Literal[""] | None = Field(default=None, description="组件路径")
    redirect: str | None = Field(default=None, description="重定向路径")

    # Vue Router 标准字段
    alias: str | list[str] | None = Field(default=None, description="路由别名")
    props: bool | dict | None = Field(default=None, description="传递给组件的 props")

    # 路由参数
    query: dict | None = Field(default=None, description="路由 query 参数（对应 route_query）")

    # 元信息
    meta: RouterMeta | None = Field(default=None, description="路由元信息")

    # 嵌套路由
    children: list["RouterVO"] | None = Field(default_factory=list, description="子路由列表")


# 支持递归引用
RouterVO.model_rebuild()
