/**
 * 部门管理相关类型定义
 * 对应后端：graphedu/common/models/dto/dept.py 和 vo/dept.py
 */

// ============================================================================
// 请求 DTO 类型
// ============================================================================

/**
 * 部门查询请求
 */
export interface DeptQueryDTO {
  /** 部门ID */
  deptId?: number
  /** 部门名称（模糊查询） */
  deptName?: string
  /** 父部门ID，0或None表示根节点 */
  parentId?: number
  /** 部门状态，对照sys_data_status（0正常 1停用） */
  status?: '0' | '1'
}

/**
 * 创建部门请求
 */
export interface DeptCreateDTO {
  /** 父部门ID（0表示根节点） */
  parentId?: number
  /** 部门名称 */
  deptName: string
  /** 部门编码（唯一标识） */
  deptKey: string
  /** 负责人 */
  leader?: string
  /** 联系电话 */
  phone?: string
  /** 联系邮箱 */
  email?: string
  /** 部门状态，对照sys_data_status（0正常 1停用） */
  status?: '0' | '1'
  /** 显示顺序 */
  sortOrder?: number
  /** 备注 */
  remark?: string
}

/**
 * 更新部门请求
 */
export interface DeptUpdateDTO {
  /** 部门ID */
  deptId: number
  /** 父部门ID */
  parentId?: number
  /** 部门名称 */
  deptName?: string
  /** 部门编码 */
  deptKey?: string
  /** 负责人 */
  leader?: string
  /** 联系电话 */
  phone?: string
  /** 联系邮箱 */
  email?: string
  /** 部门状态，对照sys_data_status（0正常 1停用） */
  status?: '0' | '1'
  /** 显示顺序 */
  sortOrder?: number
  /** 备注 */
  remark?: string
}

/**
 * 修改部门状态请求
 */
export interface DeptStatusChangeDTO {
  /** 部门ID */
  deptId: number
  /** 部门状态，对照sys_data_status（0正常 1停用） */
  status: '0' | '1'
}

// ============================================================================
// 响应 VO 类型
// ============================================================================

/**
 * 部门树节点
 */
export interface DeptTreeVO {
  /** 部门ID */
  deptId: number
  /** 部门名称 */
  deptName: string
  /** 父部门ID */
  parentId: number
  /** 部门编码 */
  deptKey: string
  /** 负责人 */
  leader?: string
  /** 联系电话 */
  phone?: string
  /** 联系邮箱 */
  email?: string
  /** 部门状态，对照sys_data_status（0正常 1停用） */
  status: string
  /** 显示顺序 */
  sortOrder: number
  /** 创建时间 */
  createTime?: string
  /** 是否有子部门 */
  hasChildren?: boolean
  /** 子部门列表 */
  children?: DeptTreeVO[]
}

/**
 * 部门详细信息
 */
export interface DeptDetailVO {
  /** 部门ID */
  deptId: number
  /** 父部门ID */
  parentId: number
  /** 部门名称 */
  deptName: string
  /** 部门编码 */
  deptKey: string
  /** 负责人 */
  leader?: string
  /** 联系电话 */
  phone?: string
  /** 联系邮箱 */
  email?: string
  /** 部门状态，对照sys_data_status（0正常 1停用） */
  status: string
  /** 显示顺序 */
  sortOrder: number
  /** 创建者ID */
  createBy?: number
  /** 创建时间 */
  createTime?: string
  /** 更新者ID */
  updateBy?: number
  /** 更新时间 */
  updateTime?: string
  /** 备注 */
  remark?: string
}

/**
 * 部门简要信息
 */
export interface DeptSimpleVO {
  /** 部门ID */
  deptId: number
  /** 部门名称 */
  deptName: string
  /** 部门编码 */
  deptKey: string
  /** 父部门ID */
  parentId: number
}
