"""功能权限管理相关 VO 模型 (View Objects - 响应模型)

职责：
1. 定义 API 响应的数据结构
2. 配置序列化规则（from_attributes=True 支持从 ORM 对象创建）
"""

from datetime import datetime

from pydantic import Field

from graphedu.common.models.vo.base import VO


class FunctionListVO(VO):
    """功能列表项 VO"""

    function_id: int = Field(description="功能ID")
    parent_id: int = Field(description="父功能ID")
    function_name: str = Field(description="功能名称")
    function_key: str | None = Field(default=None, description="权限标识（GROUP/DIVIDER 类型为 None）")
    function_type: str = Field(
        description="功能类型: DIR-目录, MENU-菜单, BUTTON-按钮, INTERFACE-接口, GROUP-菜单分组, DIVIDER-菜单分隔线"
    )
    route_path: str | None = Field(default=None, description="路由路径")
    route_cache: str | None = Field(
        default=None, description="路由路径页面是否缓存（Y是 N否，对应sys_data_option字典）"
    )
    route_query: dict | None = Field(default=None, description="路由传递参数")
    route_external: str | None = Field(default=None, description="是否外链（Y是 N否，对应sys_data_option字典）")
    component: str | None = Field(default=None, description="组件路径")
    layout_component: str | None = Field(default=None, description="布局组件路径")
    icon: str | None = Field(default=None, description="图标")
    sort_order: int = Field(description="显示顺序")
    visible: str = Field(description="是否可见（Y是 N否，对应sys_data_option字典）")
    style: dict | None = Field(default=None, description="菜单CSS样式（JSON格式）")
    option_style: dict | None = Field(default=None, description="菜单选项样式（JSON格式）")
    status: str = Field(description="状态（0正常 1停用）")
    scene: str = Field(default="admin", description="应用场景: web-日常应用, admin-管理系统, mobile-移动端")
    create_time: datetime | None = Field(default=None, description="创建时间")


class FunctionDetailVO(VO):
    """功能详细信息 VO"""

    function_id: int = Field(description="功能ID")
    parent_id: int = Field(description="父功能ID")
    function_name: str = Field(description="功能名称")
    function_key: str | None = Field(default=None, description="权限标识（GROUP/DIVIDER 类型为 None）")
    function_type: str = Field(
        description="功能类型: DIR-目录, MENU-菜单, BUTTON-按钮, INTERFACE-接口, GROUP-菜单分组, DIVIDER-菜单分隔线"
    )
    route_path: str | None = Field(default=None, description="路由路径")
    route_cache: str | None = Field(default=None, description="路由路径页面是否缓存（Y是 N否）；仅 MENU 类型有效")
    route_query: dict | None = Field(default=None, description="路由传递参数")
    route_external: str | None = Field(default=None, description="是否外链（Y是 N否）；仅 MENU 类型有效")
    component: str | None = Field(default=None, description="组件路径")
    layout_component: str | None = Field(default=None, description="布局组件路径（如: layout/CommonLayout/index）")
    icon: str | None = Field(default=None, description="图标")
    sort_order: int = Field(description="显示顺序")
    visible: str = Field(description="是否可见（Y是 N否，对应sys_data_option字典）")
    style: dict | None = Field(default=None, description="菜单CSS样式（JSON格式，使用css-in-js格式）")
    option_style: dict | None = Field(default=None, description="菜单选项样式（JSON格式）")
    status: str = Field(description="对照sys_data_status（0正常 1停用 2已删除）")
    scene: str = Field(default="admin", description="应用场景: web-日常应用, admin-管理系统, mobile-移动端")
    create_by: int | None = Field(default=None, description="创建者")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")
    remark: str | None = Field(default=None, description="备注")


class FunctionTreeBriefVO(VO):
    """功能树节点 简要 VO（用于树形选择展示）"""

    function_id: int = Field(description="功能ID")
    parent_id: int = Field(description="父功能ID")
    function_name: str = Field(description="功能名称")
    function_type: str = Field(
        description="功能类型: DIR-目录, MENU-菜单, BUTTON-按钮, INTERFACE-接口, GROUP-菜单分组, DIVIDER-菜单分隔线"
    )
    children: list["FunctionTreeBriefVO"] = Field(default_factory=list, description="子功能列表")


class FunctionTreeVO(VO):
    """功能树节点 VO（用于最外层页面树形展示）"""

    function_id: int = Field(description="功能ID")
    parent_id: int = Field(description="父功能ID")
    function_name: str = Field(description="功能名称")
    function_key: str | None = Field(default=None, description="权限标识（GROUP/DIVIDER 类型为 None）")
    function_type: str = Field(
        description="功能类型: DIR-目录, MENU-菜单, BUTTON-按钮, INTERFACE-接口, GROUP-菜单分组, DIVIDER-菜单分隔线"
    )
    route_path: str | None = Field(default=None, description="路由路径")
    route_cache: str | None = Field(default=None, description="路由页面是否缓存")
    route_external: str | None = Field(default=None, description="是否外链")
    component: str | None = Field(default=None, description="组件路径")
    layout_component: str | None = Field(default=None, description="布局组件路径（如: layout/CommonLayout/index）")
    icon: str | None = Field(default=None, description="图标")
    sort_order: int = Field(description="显示顺序")
    visible: str = Field(description="是否可见")
    status: str = Field(description="状态")
    scene: str = Field(default="admin", description="应用场景: web-日常应用, admin-管理系统, mobile-移动端")
    create_time: datetime = Field(default=None, description="创建时间")
    has_children: bool | None = Field(default=None, description="是否有子功能")
    children: list["FunctionTreeVO"] | None = Field(default_factory=list, description="子功能列表")


class RoleFunctionTreeVO(VO):
    """角色功能树 VO（用于分配权限时展示）"""

    checked_ids: list[int] = Field(default_factory=list, description="已分配的功能ID列表")
    function_trees: list[FunctionTreeVO] = Field(default_factory=list, description="功能树列表")
