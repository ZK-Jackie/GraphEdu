/**
 * 角色管理相关类型定义
 * 对应后端：graphedu/common/models/dto/role.py 和 vo/role.py
 */

// ============================================================================
// 请求 DTO 类型
// ============================================================================

/**
 * 角色查询请求
 */
export interface RoleQueryDTO {
  /** 角色名称（模糊查询） */
  roleName?: string
  /** 角色标识（模糊查询） */
  roleKey?: string
  /** 对照sys_data_status（0正常 1停用） */
  status?: '0' | '1'
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
}

/**
 * 创建角色请求
 */
export interface RoleCreateDTO {
  /** 角色名称 */
  roleName: string
  /** 角色标识（student/teacher/admin） */
  roleKey: string
  /** 显示顺序 */
  roleSort?: number
  /** 数据范围（1：全部 2：自定 3：本部门 4：本部门及以下 5：仅本人） */
  dataScope?: '1' | '2' | '3' | '4' | '5'
  /** 对照sys_data_status（0正常 1停用） */
  status?: '0' | '1'
  /** 备注 */
  remark?: string
  /** 功能权限ID列表 */
  functionIds?: number[]
}

/**
 * 更新角色请求
 */
export interface RoleUpdateDTO {
  /** 角色ID */
  roleId: number
  /** 角色名称 */
  roleName?: string
  /** 角色标识 */
  roleKey?: string
  /** 显示顺序 */
  roleSort?: number
  /** 数据范围 */
  dataScope?: '1' | '2' | '3' | '4' | '5'
  /** 对照sys_data_status（0正常 1停用） */
  status?: '0' | '1'
  /** 备注 */
  remark?: string
  /** 功能权限ID列表 */
  functionIds?: number[]
}

/**
 * 修改角色状态请求
 */
export interface RoleStatusChangeDTO {
  /** 角色ID */
  roleId: number
  /** 对照sys_data_status（0正常 1停用） */
  status: '0' | '1'
}

/**
 * 修改角色数据权限范围请求
 */
export interface RoleDatascopeChangeDTO {
  /** 角色ID */
  roleId: number
  /** 部门ID列表 */
  deptIds: number[]
  /** 数据范围（1：全部 2：自定 3：本部门 4：本部门及以下 5：仅本人） */
  dataScope: '1' | '2' | '3' | '4' | '5'
}

/**
 * 角色关联的用户查询请求
 */
export interface RoleUserQueryDTO {
  /** 角色ID（精确查询） */
  roleId?: number
  /** 用户账号 */
  userName?: string
  /** 用户昵称 */
  nickName?: string
  /** 用户邮箱 */
  email?: string
  /** 手机号码 */
  phonenumber?: string
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
}

// ============================================================================
// 响应 VO 类型
// ============================================================================

/**
 * 角色列表项
 */
export interface RoleListVO {
  /** 角色ID */
  roleId: number
  /** 角色名称 */
  roleName: string
  /** 角色标识 */
  roleKey: string
  /** 显示顺序 */
  roleSort: number
  /** 数据范围 */
  dataScope: string
  /** 对照sys_data_status（0正常 1停用 2已删除） */
  status: string
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
 * 角色详细信息
 */
export interface RoleDetailVO {
  /** 角色ID */
  roleId: number
  /** 角色名称 */
  roleName: string
  /** 角色标识 */
  roleKey: string
  /** 显示顺序 */
  roleSort: number
  /** 数据范围（1：全部 2：自定 3：本部门 4：本部门及以下 5：仅本人） */
  dataScope: string
  /** 对照sys_data_status（0正常 1停用 2已删除） */
  status: string
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
  /** 已分配的功能权限ID列表 */
  functionIds?: number[]
}

/**
 * 角色简要信息
 */
export interface RoleSimpleVO {
  /** 角色ID */
  roleId: number
  /** 角色名称 */
  roleName: string
  /** 角色标识 */
  roleKey: string
  /** 对照sys_data_status（0正常 1停用 2已删除） */
  status: string
}

/**
 * 角色关联部门响应
 */
export interface RoleDeptVO {
  /** 已选中的部门ID列表 */
  checkedIds: number[]
}

// ============================================================================
// 枚举类型
// ============================================================================

/**
 * 数据范围类型：1：全部 2：自定 3：本部门 4：本部门及以下 5：仅本人
 */
export type DataScopeType = '1' | '2' | '3' | '4' | '5'
