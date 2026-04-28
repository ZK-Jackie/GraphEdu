/**
 * 字典管理相关类型定义
 * @description 对应后端: graphedu/common/models/dto/dict.py 和 vo/dict.py
 */

/**
 * 字典类型枚举（预定义常用类型）
 * 允许其他自定义字符串类型
 * @lastUpdate 2026-02-14
 */
export type DictType =
  // 系统用户相关
  | 'sys_user_sex' // 性别
  | 'sys_user_type' // 用户类型
  | 'sys_user_cn_political_status' // 政治面貌
  | 'sys_user_cn_nation' // 民族
  | 'sys_user_cn_id_type' // 证件类型
  // 系统角色相关
  | 'sys_role_data_scope' // 角色权限范围
  // 系统基础字典
  | 'sys_language' // 语种
  | 'sys_data_status' // 数据状态
  | 'sys_data_option' // 数据选项（是/否）
  // 系统功能相关
  | 'sys_function_type' // 系统功能类型
  | 'sys_function_scene' // 系统功能应用场景
  // 系统上传相关
  | 'sys_upload_audit_status' // 上传文件审核状态
  | 'sys_upload_file_category' // 上传文件分类
  | 'sys_upload_storage_type' // 上传文件存储类型
  | 'sys_upload_access_level' // 上传文件访问级别
  // 系统日志相关
  | 'sys_oper_log_business_type' // 操作日志-业务类型
  | 'sys_oper_log_oper_type' // 操作日志-操作类型
  // 教育相关
  | 'edu_background' // 学历背景
  | 'edu_book_category' // 书籍分类
  | 'edu_student_status' // 学生状态
  | 'edu_academic_degree' // 学位
  | 'edu_professional_title' // 职称
  // 知识图谱相关
  | 'kg_build_method' // 图谱构建方法
  // 允许其他自定义字典类型
  | string

// ============================================================================
// 字典类型相关类型
// ============================================================================

/**
 * 字典类型查询请求
 */
export interface DictTypeQueryDTO {
  /** 字典名称（模糊查询） */
  dictName?: string
  /** 字典类型（模糊查询） */
  dictType?: string
  /** 状态（0正常 1停用） */
  status?: '0' | '1'
  /** 开始时间（YYYY-MM-DD） */
  beginTime?: string
  /** 结束时间（YYYY-MM-DD） */
  endTime?: string
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
}

/**
 * 创建字典类型请求
 */
export interface DictTypeCreateDTO {
  /** 字典名称 */
  dictName: string
  /** 字典类型 */
  dictType: string
  /** 状态（0正常 1停用） */
  status?: '0' | '1'
  /** 备注 */
  remark?: string
}

/**
 * 更新字典类型请求
 */
export interface DictTypeUpdateDTO {
  /** 字典主键 */
  dictId: number
  /** 字典名称 */
  dictName?: string
  /** 字典类型 */
  dictType?: string
  /** 状态 */
  status?: '0' | '1'
  /** 备注 */
  remark?: string
}

/**
 * 字典类型列表项
 */
export interface DictTypeListVO {
  /** 字典主键 */
  dictId: number
  /** 字典名称 */
  dictName: string
  /** 字典类型 */
  dictType: string
  /** 字典类型数据状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status: string
  /** 创建时间 */
  createTime?: string
  /** 备注 */
  remark?: string
}

/**
 * 字典类型详情
 */
export interface DictTypeDetailVO {
  /** 字典主键 */
  dictId: number
  /** 字典名称 */
  dictName: string
  /** 字典类型 */
  dictType: string
  /** 字典类型数据状态，对照 sys_data_status（0正常 1停用 2已删除） */
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

// ============================================================================
// 字典数据相关类型
// ============================================================================

/**
 * 字典数据查询请求
 */
export interface DictDataQueryDTO {
  /** 字典类型（精确查询） */
  dictType?: string
  /** 字典标签（模糊查询） */
  dictLabel?: string
  /** 状态（0正常 1停用） */
  status?: '0' | '1'
  /** 开始时间（YYYY-MM-DD） */
  beginTime?: string
  /** 结束时间（YYYY-MM-DD） */
  endTime?: string
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
}

/**
 * 创建字典数据请求
 */
export interface DictDataCreateDTO {
  /** 字典标签 */
  dictLabel: string
  /** 字典键值 */
  dictValue: string
  /** 字典类型 */
  dictType: string
  /** 字典排序 */
  dictSort?: number
  /** 样式属性（JSONB格式） */
  style?: Record<string, any>
  /** 颜色主题（success | processing | error | warning | default） */
  color?: string
  /** 图标（Ant Design Vue图标名称） */
  icon?: string
  /** 是否带边框（Y是 N否） */
  bordered?: 'Y' | 'N'
  /** 是否默认（Y是 N否） */
  isDefault?: 'Y' | 'N'
  /** 字典值数据状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status?: '0' | '1'
  /** 备注 */
  remark?: string
}

/**
 * 更新字典数据请求
 */
export interface DictDataUpdateDTO {
  /** 字典编码 */
  dictCode: number
  /** 字典标签 */
  dictLabel?: string
  /** 字典键值 */
  dictValue?: string
  /** 字典类型 */
  dictType?: string
  /** 字典排序 */
  dictSort?: number
  /** 样式属性（JSONB格式） */
  style?: Record<string, any>
  /** 颜色主题（success | processing | error | warning | default） */
  color?: string
  /** 图标（Ant Design Vue图标名称） */
  icon?: string
  /** 是否带边框（Y是 N否） */
  bordered?: 'Y' | 'N'
  /** 是否默认 */
  isDefault?: 'Y' | 'N'
  /** 字典值数据状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status?: '0' | '1'
  /** 备注 */
  remark?: string
}

/**
 * 字典数据列表项
 */
export interface DictDataListVO {
  /** 字典编码 */
  dictCode: number
  /** 字典排序 */
  dictSort: number
  /** 字典标签 */
  dictLabel: string
  /** 字典键值 */
  dictValue: string
  /** 字典类型 */
  dictType: string
  /** 样式属性（JSONB格式） */
  style?: Record<string, any>
  /** 颜色主题（success | processing | error | warning | default） */
  color: string
  /** 图标（Ant Design Vue图标名称） */
  icon?: string
  /** 是否带边框（Y是 N否） */
  bordered: 'Y' | 'N'
  /** 是否默认（Y是 N否） */
  isDefault: string
  /** 字典值数据状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status: string
  /** 创建时间 */
  createTime?: string
  /** 备注 */
  remark?: string
}

/**
 * 字典数据详情
 */
export interface DictDataDetailVO {
  /** 字典编码 */
  dictCode: number
  /** 字典排序 */
  dictSort: number
  /** 字典标签 */
  dictLabel: string
  /** 字典键值 */
  dictValue: string
  /** 字典类型 */
  dictType: string
  /** 样式属性（JSONB格式） */
  style?: Record<string, any>
  /** 颜色主题（success | processing | error | warning | default） */
  color: string
  /** 图标（Ant Design Vue图标名称） */
  icon?: string
  /** 是否带边框（Y是 N否） */
  bordered: 'Y' | 'N'
  /** 是否默认（Y是 N否） */
  isDefault: string
  /** 字典值数据状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status: string
  /** 删除标志（0代表存在 2代表删除） */
  delFlag: string
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
 * 字典数据简化VO（用于下拉框等场景）
 */
export interface DictDataSimpleVO {
  /** 字典标签 */
  dictLabel: string
  /** 字典键值 */
  dictValue: string
  /** 样式属性（JSONB格式） */
  style?: Record<string, any>
  /** 颜色主题（success | processing | error | warning | default） */
  color: string
  /** 图标（Ant Design Vue图标名称） */
  icon?: string
  /** 是否带边框（Y是 N否） */
  bordered?: 'Y' | 'N'
}
