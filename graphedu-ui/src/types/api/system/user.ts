/**
 * 用户管理相关类型定义
 * 对应后端：graphedu/common/models/dto/user.py 和 vo/user.py
 */

import type { CSSProperties } from 'vue'
import type { StudentDetailVO, StudentListVO } from '@/types/api/education/student.ts'
import type { TeacherDetailVO, TeacherListVO } from '@/types/api/education/teacher.ts'

// ============================================================================
// 请求 DTO 类型
// ============================================================================

/**
 * 用户名登录请求
 */
export interface UserLoginByUsernameDTO {
  /** 用户名称 */
  username: string
  /** 用户密码 */
  password: string
  /** 验证码 */
  code?: string
  /** 会话编号 */
  uuid?: string
}

/**
 * 登录响应
 */
export interface UserLoginResponseDTO {
  /** 访问令牌 */
  accessToken: string
  /** 令牌类型 */
  tokenType: string
  /** 令牌过期时间，单位秒 */
  expiresIn?: number
}

/**
 * 手机号登录请求
 */
export interface UserLoginByPhoneDTO {
  /** 手机号码 */
  phonenumber: string
  /** 用户密码 */
  password: string
  /** 验证码 */
  code?: string
  /** 会话编号 */
  uuid?: string
}

/**
 * 学号登录请求
 */
export interface UserLoginByStudentNoDTO {
  /** 学号 */
  studentNo: string
  /** 用户密码 */
  password: string
  /** 验证码 */
  code?: string
  /** 会话编号 */
  uuid?: string
}

/**
 * 工号登录请求
 */
export interface UserLoginByTeacherNoDTO {
  /** 工号 */
  teacherNo: string
  /** 用户密码 */
  password: string
  /** 验证码 */
  code?: string
  /** 会话编号 */
  uuid?: string
}

/**
 * 忘记密码 - 发送短信验证码请求
 */
export interface ForgotPasswordSendCodeDTO {
  /** 手机号码 */
  phonenumber: string
}

/**
 * 忘记密码 - 重置密码请求
 */
export interface ForgotPasswordResetDTO {
  /** 手机号码 */
  phonenumber: string
  /** 短信验证码 */
  smsCode: string
  /** 新密码 */
  newPassword: string
  /** 确认新密码 */
  confirmPassword: string
}

/**
 * 用户名注册请求
 */
export interface UserRegisterByUsernameDTO {
  /** 用户名称 */
  username: string
  /** 用户密码 */
  password: string
  /** 用户二次确认密码 */
  confirmPassword: string
  /** 验证码 */
  code?: string
  /** 会话编号 */
  uuid?: string
}

/**
 * 重置密码请求
 */
export interface UserResetPasswordDTO {
  /** 旧密码 */
  oldPassword?: string
  /** 新密码 */
  newPassword?: string
  /** 短信验证码 */
  smsCode?: string
}

/**
 * 用户查询请求
 */
export interface UserQueryDTO {
  /** 用户ID */
  userId?: number
  /** 用户账号 */
  userName?: string
  /** 用户昵称 */
  nickName?: string
  /** 用户邮箱 */
  email?: string
  /** 手机号码 */
  phonenumber?: string
  /** 用户类型列表 */
  userTypes?: number[]
  /** 对照sys_data_status（0正常 1停用） */
  status?: '0' | '1'
  /** 角色ID列表 */
  roleIds?: number[]
  /** 部门ID列表 */
  deptIds?: number[]
  /** 创建开始时间 */
  beginTime?: string
  /** 创建结束时间 */
  endTime?: string
  /** 页码 */
  page?: number
  /** 每页数量 */
  size?: number
}

/**
 * 创建用户请求
 */
export interface UserCreateDTO {
  /** 用户账号 */
  userName: string
  /** 用户昵称 */
  nickName: string
  /** 用户密码 */
  password: string
  /** 用户邮箱 */
  email?: string
  /** 手机号码 */
  phonenumber?: string
  /** 用户类型: 0-超级管理员, 1-学生, 2-教师, 3-管理员, 4-访客 */
  userType?: number
  /** 对照sys_data_status（0正常 1停用） */
  status?: '0' | '1'
  /** 备注 */
  remark?: string
  /** 角色ID列表 */
  roleIds?: number[]
  /** 部门ID列表 */
  deptIds?: number[]
  // 内联学生信息字段（当 userType = 1 时使用）
  /** 学生真实姓名 */
  studentRealName?: string
  /** 学号 */
  studentNo?: string
  /** 学院 */
  studentFaculty?: string
  /** 专业 */
  studentMajor?: string
  /** 年级 */
  studentGrade?: string
  /** 班级 */
  studentClassName?: string
  // 内联教师信息字段（当 userType = 2 时使用）
  /** 教师真实姓名 */
  teacherRealName?: string
  /** 工号 */
  teacherNo?: string
  /** 所属学院 */
  teacherFaculty?: string
  /** 职称 */
  teacherTitle?: string
  /** 研究方向 */
  teacherResearchDirection?: string
}

/**
 * 更新用户请求
 */
export interface UserUpdateDTO {
  /** 用户ID */
  userId: number
  /** 用户昵称 */
  nickName?: string
  /** 用户邮箱 */
  email?: string
  /** 手机号码 */
  phonenumber?: string
  /** 头像文件ID */
  avatarFileId?: number
  /** 账号状态 */
  status?: string
  /** 备注 */
  remark?: string
  /** 最后登录IP */
  loginIp?: string
  /** 最后登录时间 */
  loginDate?: string
  /** 角色ID列表 */
  roleIds?: number[]
  /** 部门ID列表 */
  deptIds?: number[]
  // 内联学生信息字段（当 userType = 1 时使用）
  /** 学生真实姓名 */
  studentRealName?: string
  /** 学号 */
  studentNo?: string
  /** 学院 */
  studentFaculty?: string
  /** 专业 */
  studentMajor?: string
  /** 年级 */
  studentGrade?: string
  /** 班级 */
  studentClassName?: string
  // 内联教师信息字段（当 userType = 2 时使用）
  /** 教师真实姓名 */
  teacherRealName?: string
  /** 工号 */
  teacherNo?: string
  /** 所属学院 */
  teacherFaculty?: string
  /** 职称 */
  teacherTitle?: string
  /** 研究方向 */
  teacherResearchDirection?: string
}

/**
 * 管理员重置用户密码请求
 */
export interface UserPasswordResetDTO {
  /** 用户ID */
  userId: number
  /** 新密码 */
  password: string
}

/**
 * 修改用户状态请求
 */
export interface UserStatusChangeDTO {
  /** 用户ID */
  userId: number
  /** 对照sys_data_status（0正常 1停用） */
  status: '0' | '1'
}

/**
 * 更新个人信息请求
 */
export interface UserProfileUpdateDTO {
  /** 用户昵称 */
  nickName?: string
  /** 用户邮箱 */
  email?: string
  /** 手机号码 */
  phonenumber?: string
  /** 备注 */
  remark?: string
}

/**
 * 更新用户角色关联请求
 */
export interface UserRoleUpdateDTO {
  /** 用户ID */
  userId: number
  /** 角色ID列表 */
  roleIds: number[]
}

// ============================================================================
// 响应 VO 类型
// ============================================================================

/**
 * 用户详细信息
 */
export interface UserDetailVO {
  /** 用户ID */
  userId: number
  /** 登录账号 */
  userName: string
  /** 用户昵称 */
  nickName: string
  /** 用户邮箱 */
  email?: string
  /** 手机号码 */
  phonenumber?: string
  /** 头像文件ID */
  avatarFileId?: number
  /** 头像文件路径 */
  avatarPath?: string
  /** 用户类型: 1-学生, 2-教师, 3-管理员 */
  userType: number
  /** 对照sys_data_status（0正常 1停用） */
  status: string
  /** 最后登录IP */
  loginIp?: string
  /** 最后登录时间 */
  loginDate?: string
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
  /** 部门ID列表 */
  deptIds?: number[]
  /** 角色ID列表 */
  roleIds?: number[]
  /** 关联的学生信息（最多1个） */
  student?: StudentDetailVO
  /** 关联的教师信息（最多1个） */
  teacher?: TeacherDetailVO
}

/**
 * 用户列表项
 */
export interface UserListVO {
  /** 用户ID */
  userId: number
  /** 登录账号 */
  userName: string
  /** 用户昵称 */
  nickName: string
  /** 用户邮箱 */
  email?: string
  /** 手机号码 */
  phonenumber?: string
  /** 头像文件ID */
  avatarFileId?: number
  /** 用户类型: 1-学生, 2-教师, 3-管理员 */
  userType: number
  /** 对照sys_data_status（0正常 1停用） */
  status: string
  /** 创建时间 */
  createTime?: string
  /** 主部门ID */
  deptId?: number
  /** 主部门名称 */
  deptName?: string
  /** 关联的学生信息（最多1个） */
  student?: StudentListVO
  /** 关联的教师信息（最多1个） */
  teacher?: TeacherListVO
}

/**
 * 用户个人信息
 */
export interface UserProfileVO {
  /** 用户详细信息 */
  user: UserDetailVO
  /** 用户角色标识列表 */
  roleKeys?: string[]
  /** 用户角色名称列表 */
  roleNames?: string[]
  /** 用户部门标识列表 */
  deptKeys?: string[]
  /** 用户部门名称列表 */
  deptNames?: string[]
}

/**
 * 用户角色列表响应
 */
export interface UserRoleListVO {
  /** 用户ID */
  userId: number
  /** 用户名称 */
  userName: string
  /** 用户当前角色ID列表 */
  roleIds: number[]
  /** 所有角色列表 */
  roles: any[]
}

/**
 * 认证后的当前用户详细信息
 */
export interface AuthCurrentUserDetailVO {
  /** 部门ID列表 */
  deptIds: number[]
  /** 角色ID列表 */
  roleIds: number[]
  /** 部门信息列表 */
  depts: any[]
  /** 角色信息列表 */
  roles: any[]
  /** 用户信息 */
  user: UserDetailVO
  /** 用户头像URL */
  avatarUrl?: string
  /** 学生信息 */
  student?: StudentDetailVO
  /** 教师信息 */
  teacher?: TeacherDetailVO
}

/**
 * 认证后的当前用户信息
 */
export interface AuthCurrentUserVO {
  /** 会话ID */
  sessionId?: string
  /** function_key字符串列表 */
  permissions: string[]
  /** role_key字符串列表 */
  roleKeys: string[]
  /** 用户信息 */
  detail: AuthCurrentUserDetailVO
}

/**
 * 路由信息（对齐 Vue Router 的 RouteRecordRaw）
 */
export interface Router {
  /** 路由路径（必填） */
  path: string
  /** 路由名称 */
  name?: string
  /** 组件路径 */
  component?: string
  /** 重定向路径 */
  redirect?: string
  /** 路由别名 */
  alias?: string | string[]
  /** 传递给组件的 props */
  props?: boolean | Record<string, any>
  /** 路由 query 参数 */
  query?: Record<string, any>
  /** 路由元信息 */
  meta?: RouterMeta
  /** 子路由 */
  children?: Router[]
}

/**
 * 路由元信息（对齐 Vue Router 的 meta 字段，并根据 sys_function 丰富）
 */
export interface RouterMeta {
  /** 权限标识（唯一标识，对应 function_key） */
  key: string
  /** 页面标题（对应 function_name） */
  title: string
  /** 菜单图标（对应 icon） */
  icon?: string
  /** 是否缓存页面（对应 route_cache，0-不缓存 1-缓存） */
  keepAlive?: boolean
  /** 是否固定在标签栏 */
  affix?: boolean
  /** 外链地址（当 route_external=1 时有效） */
  link?: string
  /** 是否隐藏（对应 visible=0 时为 true） */
  hidden?: boolean
  /** 是否启用（对应 status=0 时为 true） */
  enabled?: boolean
  /** 显示顺序（对应 sort_order） */
  order?: number
  /** 菜单CSS样式（JSON格式，使用css-in-js格式，对应 style） */
  style?: CSSProperties
  /** 菜单选项样式（JSON格式，对应 option_style） */
  optionStyle?: Record<string, boolean | string>
}
