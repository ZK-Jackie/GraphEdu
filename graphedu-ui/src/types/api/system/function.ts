/**
 * 功能权限管理相关类型定义
 * 对应后端：graphedu/common/models/dto/function.py 和 vo/function.py
 */

// ============================================================================
// 请求 DTO 类型
// ============================================================================

/**
 * 功能类型枚举
 */
export type FunctionType = 'DIR' | 'MENU' | 'BUTTON' | 'INTERFACE' | 'GROUP' | 'DIVIDER'

/**
 * 功能查询请求
 */
export interface FunctionQueryDTO {
  /** 功能名称（模糊查询） */
  functionName?: string
  /** 功能状态，对照 sys_data_status（0正常 1停用） */
  status?: '0' | '1'
  /** 是否可见（Y是 N否，对应 sys_data_option 字典） */
  visible?: 'Y' | 'N'
  /** 功能类型: DIR-目录, MENU-菜单, BUTTON-按钮, INTERFACE-接口, GROUP-分组, DIVIDER-分隔线 */
  functionType?: FunctionType
  /** 应用场景: web-日常应用, admin-管理系统, mobile-移动端 */
  scene?: string
}

/**
 * 创建功能请求
 */
export interface FunctionCreateDTO {
  /** 父功能ID（0表示根节点） */
  parentId?: number
  /** 功能名称 */
  functionName: string
  /** 权限标识（如: student:list, course:add）；GROUP/DIVIDER 类型无需填写 */
  functionKey?: string
  /** 功能类型: DIR-目录, MENU-菜单, BUTTON-按钮, INTERFACE-接口, GROUP-分组, DIVIDER-分隔线 */
  functionType: FunctionType
  /** 路由路径 */
  routePath?: string
  /** 路由页面是否缓存（N不缓存 Y缓存）；仅 MENU 类型有效 */
  routeCache?: 'N' | 'Y'
  /** 路由传递参数（JSON格式） */
  routeQuery?: Record<string, any>
  /** 是否外链（N否 Y是）；仅 MENU 类型有效 */
  routeExternal?: 'N' | 'Y'
  /** 组件路径 */
  component?: string
  /** 布局组件路径（如: layout/CommonLayout/index, layout/WorkbenchLayout/index） */
  layoutComponent?: string
  /** 菜单图标 */
  icon?: string
  /** 显示顺序 */
  sortOrder?: number
  /** 是否可见（N隐藏 Y显示） */
  visible?: 'N' | 'Y'
  /** 菜单CSS样式（JSON格式，使用css-in-js格式） */
  style?: Record<string, any>
  /** 菜单选项样式（JSON格式） */
  optionStyle?: Record<string, any>
  /** 功能状态，对照 sys_data_status（0正常 1停用） */
  status?: '0' | '1'
  /** 应用场景: web-日常应用, admin-管理系统, mobile-移动端 */
  scene?: string
  /** 备注 */
  remark?: string
}

/**
 * 更新功能请求
 */
export interface FunctionUpdateDTO {
  /** 功能ID */
  functionId: number
  /** 父功能ID */
  parentId?: number
  /** 功能名称 */
  functionName?: string
  /** 权限标识 */
  functionKey?: string
  /** 功能类型 */
  functionType?: FunctionType
  /** 路由路径 */
  routePath?: string
  /** 路由页面是否缓存（N不缓存 Y缓存）；仅 MENU 类型有效 */
  routeCache?: 'N' | 'Y'
  /** 路由传递参数 */
  routeQuery?: Record<string, any>
  /** 是否外链（N否 Y是）；仅 MENU 类型有效 */
  routeExternal?: 'N' | 'Y'
  /** 组件路径 */
  component?: string
  /** 布局组件路径（如: layout/CommonLayout/index, layout/WorkbenchLayout/index） */
  layoutComponent?: string
  /** 菜单图标 */
  icon?: string
  /** 显示顺序 */
  sortOrder?: number
  /** 是否可见（N隐藏 Y显示） */
  visible?: 'N' | 'Y'
  /** 菜单CSS样式（JSON格式，使用css-in-js格式） */
  style?: Record<string, any>
  /** 菜单选项样式（JSON格式） */
  optionStyle?: Record<string, any>
  /** 功能状态，对照 sys_data_status（0正常 1停用） */
  status?: '0' | '1'
  /** 应用场景: web-日常应用, admin-管理系统, mobile-移动端 */
  scene?: string
  /** 备注 */
  remark?: string
}

// ============================================================================
// 响应 VO 类型
// ============================================================================

/**
 * 功能树节点
 */
export interface FunctionTreeVO {
  /** 功能ID */
  functionId: number
  /** 父功能ID */
  parentId: number
  /** 功能名称 */
  functionName: string
  /** 权限标识；GROUP/DIVIDER 类型为 undefined */
  functionKey?: string
  /** 功能类型，对照 sys_function_type（DIR目录, MENU菜单, BUTTON按钮, INTERFACE接口, GROUP菜单分组, DIVIDER菜单分隔线） */
  functionType: FunctionType
  /** 路由路径 */
  routePath?: string
  /** 路由路径页面是否缓存，对应 sys_data_option（Y是 N否）；仅 MENU 类型有效 */
  routeCache?: string
  /** 是否外链，对应 sys_data_option（Y是 N否）；仅 MENU 类型有效 */
  routeExternal?: string
  /** 组件路径 */
  component?: string
  /** 布局组件路径（如: layout/CommonLayout/index） */
  layoutComponent?: string
  /** 图标 */
  icon?: string
  /** 菜单CSS样式（JSON格式，使用css-in-js格式） */
  style?: Record<string, any>
  /** 菜单选项样式（JSON格式） */
  optionStyle?: Record<string, any>
  /** 路由传递参数（JSON格式） */
  routeQuery?: Record<string, any>
  /** 显示顺序 */
  sortOrder: number
  /** 是否可见，对应 sys_data_option（Y是 N否） */
  visible: string
  /** 功能状态，对照 sys_data_status（0正常 1停用） */
  status: string
  /** 应用场景，对照 sys_function_scene（web日常应用 admin管理系统 userInfo个人中心） */
  scene: string
  /** 创建时间 */
  createTime?: string
  /** 是否有子功能 */
  hasChildren?: boolean
  /** 子功能列表 */
  children?: FunctionTreeVO[]
}

/**
 * 功能树节点（简要版，用于下拉选择）
 */
export interface FunctionTreeBriefVO {
  /** 功能ID */
  functionId: number
  /** 父功能ID */
  parentId: number
  /** 功能名称 */
  functionName: string
  /** 功能类型: DIR-目录, MENU-菜单, BUTTON-按钮, INTERFACE-接口, GROUP-分组, DIVIDER-分隔线 */
  functionType: FunctionType
  /** 子功能列表 */
  children?: FunctionTreeBriefVO[]
}

/**
 * 功能详细信息
 */
export interface FunctionDetailVO {
  /** 功能ID */
  functionId: number
  /** 父功能ID */
  parentId: number
  /** 功能名称 */
  functionName: string
  /** 权限标识；GROUP/DIVIDER 类型为 undefined */
  functionKey?: string
  /** 功能类型: DIR-目录, MENU-菜单, BUTTON-按钮, INTERFACE-接口, GROUP-分组, DIVIDER-分隔线 */
  functionType: FunctionType
  /** 路由路径 */
  routePath?: string
  /** 路由页面是否缓存（N不缓存 Y缓存）；仅 MENU 类型有效 */
  routeCache?: string
  /** 路由传递参数 */
  routeQuery?: Record<string, any>
  /** 是否外链（N否 Y是）；仅 MENU 类型有效 */
  routeExternal?: string
  /** 组件路径 */
  component?: string
  /** 布局组件路径（如: layout/CommonLayout/index） */
  layoutComponent?: string
  /** 图标 */
  icon?: string
  /** 菜单CSS样式（JSON格式，使用css-in-js格式） */
  style?: Record<string, any>
  /** 菜单选项样式（JSON格式） */
  optionStyle?: Record<string, any>
  /** 显示顺序 */
  sortOrder: number
  /** 是否可见（0隐藏 1显示） */
  visible: string
  /** 功能状态，对照 sys_data_status（0正常 1停用） */
  status: string
  /** 应用场景: web-日常应用, admin-管理系统, mobile-移动端 */
  scene: string
  /** 创建者 */
  createBy?: number
  /** 创建时间 */
  createTime?: string
  /** 更新者 */
  updateBy?: number
  /** 更新时间 */
  updateTime?: string
  /** 备注 */
  remark?: string
}

/**
 * 角色功能树（用于分配权限时展示）
 */
export interface RoleFunctionTreeVO {
  /** 已分配的功能ID列表 */
  checkedIds: number[]
  /** 功能树列表 */
  functionTrees: FunctionTreeVO[]
}
