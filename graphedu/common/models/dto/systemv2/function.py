"""功能权限管理相关 DTO 模型

职责：
1. 定义 API 请求验证的数据结构
2. 为 CRUD 操作设置不同的字段约束
"""

from typing import Literal

from pydantic import Field, field_validator, model_validator

from graphedu.common.models.dto.base import DTO


class FunctionQueryDTO(DTO):
    """功能查询 DTO

    用于查询功能权限列表

    Attributes:
        function_name: 功能名称（模糊查询）
        status: 功能状态（0正常 1停用）
        visible: 是否可见（0隐藏 1显示）
        function_type: 功能类型（DIR-目录, MENU-菜单, BUTTON-按钮, INTERFACE-接口, GROUP-菜单分组, DIVIDER-菜单分隔线）
        scene: 应用场景（web-日常应用, admin-管理系统, mobile-移动端）
    """

    function_name: str | None = Field(default=None, description="功能名称（模糊查询）")
    status: Literal["0", "1"] | None = Field(default=None, description="对照sys_data_status（0正常 1停用）")
    visible: Literal["N", "Y"] | None = Field(
        default=None, description="是否可见（Y是 N否，对应 sys_data_option 字典）"
    )
    function_type: str | None = Field(
        default=None,
        description="功能类型: DIR-目录, MENU-菜单, BUTTON-按钮, INTERFACE-接口, GROUP-菜单分组, DIVIDER-菜单分隔线",
    )
    scene: str | None = Field(default=None, description="应用场景: web-日常应用, admin-管理系统, mobile-移动端")


class FunctionCreateDTO(DTO):
    """创建功能 DTO - 所有必填字段必须有值

    用于创建新的功能权限

    Attributes:
        parent_id: 父功能 ID（0表示根节点）
        function_name: 功能名称
        function_key: 权限标识（如: student:list, course:add）
        function_type: 功能类型（1-目录, 2-菜单, 3-按钮, 4-接口）
        route_path: 路由路径（可选）
        route_cache: 路由页面是否缓存（0不缓存 1缓存）
        route_query: 路由传递参数（可选，JSON 格式）
        route_external: 是否外链（0否 1是）
        component: 组件路径（可选）
        icon: 菜单图标（可选）
        sort_order: 显示顺序
        visible: 是否可见（0隐藏 1显示）
        style: 菜单CSS样式（可选，JSON格式）
        option_style: 菜单选项样式（可选，JSON格式）
        status: 状态（0正常 1停用）
        scene: 应用场景（web/admin/mobile）
        remark: 备注（可选）
    """

    parent_id: int = Field(default=0, description="父功能ID（0表示根节点）")
    function_name: str = Field(description="功能名称", min_length=1, max_length=50)
    function_key: str | None = Field(
        default=None,
        description="权限标识（如: student:list, course:add）；GROUP/DIVIDER 类型无需填写",
        min_length=1,
        max_length=128,
    )
    function_type: str = Field(
        description="功能类型: DIR-目录, MENU-菜单, BUTTON-按钮, INTERFACE-接口, GROUP-菜单分组, DIVIDER-菜单分隔线"
    )
    route_path: str | None = Field(default=None, description="路由路径", max_length=128)
    route_cache: Literal["N", "Y"] | None = Field(
        default=None, description="路由路径页面是否缓存（Y是 N否，对应sys_data_option字典）；仅 MENU 类型有效"
    )
    route_query: dict | None = Field(default=None, description="路由传递参数（JSON格式）")
    route_external: Literal["N", "Y"] | None = Field(
        default=None, description="是否外链（Y是 N否，对应sys_data_option字典）；仅 MENU 类型有效"
    )
    component: str | None = Field(default=None, description="组件路径", max_length=256)
    layout_component: str | None = Field(
        default=None, description="布局组件路径（如: layout/CommonLayout/index）", max_length=256
    )
    icon: str | None = Field(default=None, description="菜单图标", max_length=128)
    sort_order: int = Field(default=0, description="显示顺序")
    visible: Literal["N", "Y"] = Field(default="Y", description="是否可见（Y是 N否，对应sys_data_option字典）")
    style: dict | None = Field(default=None, description="菜单CSS样式（JSON格式，使用css-in-js格式）")
    option_style: dict | None = Field(default=None, description="菜单选项样式（JSON格式）")
    status: Literal["0", "1"] = Field(default="0", description="对照sys_data_status（0正常 1停用）")
    scene: str = Field(default="admin", description="应用场景: web-日常应用, admin-管理系统, mobile-移动端")
    remark: str | None = Field(default=None, description="备注", max_length=500)

    @field_validator("route_external", mode="before")
    @classmethod
    def validate_external_link(cls, v: str, info) -> Literal["N", "Y"]:
        """验证外链地址格式

        如果是外链，验证 route_path 是否以 http 开头

        Args:
            v: route_external 的值
            info: 验证上下文信息

        Returns:
            验证通过后的值

        Raises:
            ValueError: 外链地址格式不正确
        """
        if v == "Y":
            # 如果是外链，需要验证route_path是否以http开头
            route_path = info.data.get("route_path")
            if route_path and not route_path.startswith(("http://", "https://")):
                raise ValueError("外链地址必须以http://或https://开头")
        return v

    @model_validator(mode="after")
    def type_filter(self) -> "FunctionCreateDTO":
        """根据功能类型过滤无关字段

        不同功能类型只允许特定字段，清除不相关的字段以避免数据污染
        """
        function_type = self.function_type

        # GROUP/DIVIDER 不需要权限标识；其他类型必须填写
        if function_type not in ("GROUP", "DIVIDER") and not self.function_key:
            raise ValueError("权限标识不能为空")

        # BUTTON 和 INTERFACE：只需要基础字段 + functionKey
        if function_type in ("BUTTON", "INTERFACE"):
            self.route_path = None
            self.route_cache = None
            self.route_query = None
            self.route_external = None
            self.component = None
            self.layout_component = None
            self.icon = None
            self.style = None
            self.option_style = None

        # DIR：允许路由路径和组件字段，但不允许高级路由选项
        elif function_type == "DIR":
            self.route_query = None
            self.route_external = None
            self.route_cache = None
            self.style = None
            self.option_style = None

        # GROUP：菜单分组只需要基础字段
        elif function_type == "GROUP":
            self.function_key = None
            self.route_path = None
            self.route_cache = None
            self.route_query = None
            self.route_external = None
            self.component = None
            self.layout_component = None
            self.icon = None
            self.style = None
            self.option_style = None

        # DIVIDER：分隔线字段最少
        elif function_type == "DIVIDER":
            self.function_key = None
            self.route_path = None
            self.route_cache = None
            self.route_query = None
            self.route_external = None
            self.component = None
            self.layout_component = None
            self.icon = None
            self.style = None
            self.option_style = None
            self.remark = None

        # MENU 类型不过滤，允许所有字段
        return self


class FunctionUpdateDTO(DTO):
    """更新功能 DTO - 所有字段可选，仅更新提供的字段

    用于更新功能权限信息

    Attributes:
        function_id: 功能 ID
        parent_id: 父功能 ID（可选）
        function_name: 功能名称（可选）
        function_key: 权限标识（可选）
        function_type: 功能类型（可选）
        route_path: 路由路径（可选）
        route_cache: 路由页面是否缓存（可选）
        route_query: 路由传递参数（可选）
        route_external: 是否外链（可选）
        component: 组件路径（可选）
        icon: 菜单图标（可选）
        sort_order: 显示顺序（可选）
        visible: 是否可见（可选）
        style: 菜单CSS样式（可选，JSON格式）
        option_style: 菜单选项样式（可选，JSON格式）
        status: 状态（可选）
        scene: 应用场景（可选）
        remark: 备注（可选）
    """

    function_id: int = Field(description="功能ID")
    parent_id: int | None = Field(default=None, description="父功能ID")
    function_name: str | None = Field(default=None, description="功能名称", max_length=50)
    function_key: str | None = Field(default=None, description="权限标识", max_length=128)
    function_type: str | None = Field(
        default=None,
        description="功能类型: DIR-目录, MENU-菜单, BUTTON-按钮, INTERFACE-接口, GROUP-菜单分组, DIVIDER-菜单分隔线",
    )
    route_path: str | None = Field(default=None, description="路由路径", max_length=128)
    route_cache: Literal["N", "Y"] | None = Field(
        default=None, description="路由路径页面是否缓存（Y是 N否，对应sys_data_option字典）"
    )
    route_query: dict | None = Field(default=None, description="路由传递参数（JSON格式）")
    route_external: Literal["N", "Y"] | None = Field(
        default=None, description="是否外链（Y是 N否，对应sys_data_option字典）"
    )
    component: str | None = Field(default=None, description="组件路径", max_length=256)
    layout_component: str | None = Field(
        default=None, description="布局组件路径（如: layout/CommonLayout/index）", max_length=256
    )
    icon: str | None = Field(default=None, description="菜单图标", max_length=128)
    sort_order: int | None = Field(default=None, description="显示顺序")
    visible: Literal["N", "Y"] | None = Field(default=None, description="是否可见（Y是 N否，对应sys_data_option字典）")
    style: dict | None = Field(default=None, description="菜单CSS样式（JSON格式，使用css-in-js格式）")
    option_style: dict | None = Field(default=None, description="菜单选项样式（JSON格式）")
    status: Literal["0", "1"] | None = Field(default=None, description="对照sys_data_status（0正常 1停用）")
    scene: str | None = Field(default=None, description="应用场景: web-日常应用, admin-管理系统, mobile-移动端")
    remark: str | None = Field(default=None, description="备注", max_length=500)

    @model_validator(mode="after")
    def type_filter(self) -> "FunctionUpdateDTO":
        """根据功能类型过滤无关字段

        不同功能类型只允许特定字段，清除不相关的字段以避免数据污染
        """
        function_type = self.function_type
        if not function_type:
            return self

        # BUTTON 和 INTERFACE：只需要基础字段 + functionKey
        if function_type in ("BUTTON", "INTERFACE"):
            self.route_path = None
            self.route_cache = None
            self.route_query = None
            self.route_external = None
            self.component = None
            self.layout_component = None
            self.icon = None
            self.style = None
            self.option_style = None

        # DIR：允许路由路径和组件字段，但不允许高级路由选项
        elif function_type == "DIR":
            self.route_query = None
            self.route_external = None
            self.route_cache = None
            self.style = None
            self.option_style = None

        # GROUP：菜单分组只需要基础字段
        elif function_type == "GROUP":
            self.function_key = None
            self.route_path = None
            self.route_cache = None
            self.route_query = None
            self.route_external = None
            self.component = None
            self.layout_component = None
            self.icon = None
            self.style = None
            self.option_style = None

        # DIVIDER：分隔线字段最少
        elif function_type == "DIVIDER":
            self.function_key = None
            self.route_path = None
            self.route_cache = None
            self.route_query = None
            self.route_external = None
            self.component = None
            self.layout_component = None
            self.icon = None
            self.style = None
            self.option_style = None
            self.remark = None

        # MENU 类型不过滤，允许所有字段
        return self


class RoleFunctionTreeDTO(DTO):
    """角色功能树 DTO（用于分配权限）

    用于角色分配权限时返回功能树

    Attributes:
        functions: 功能树列表
        checked_keys: 已选中的功能 ID 列表
    """

    functions: list[dict] = Field(description="功能树列表")
    checked_keys: list[int] = Field(description="已选中的功能ID列表")
