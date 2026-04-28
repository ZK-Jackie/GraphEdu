/**
 * 认证相关 API
 * 对应后端：graphedu/api/services/system/auth.py
 */
import request from '@/utils/request'
import type { ResponseType, Empty } from '@/types/api/common.ts'
import type {
  UserLoginByUsernameDTO,
  UserLoginByPhoneDTO,
  UserLoginByStudentNoDTO,
  UserLoginByTeacherNoDTO,
  UserLoginResponseDTO,
  UserRegisterByUsernameDTO,
  ForgotPasswordSendCodeDTO,
  ForgotPasswordResetDTO,
  AuthCurrentUserVO,
  UserDetailVO,
} from '@/types/api/system/user.ts'
import type { RouterVO } from '@/types/api/common/auth.ts'
import type { FunctionTreeVO } from '@/types/api/system/function.ts'
import type { CaptchaDTO, TurnstileValidateDTO, TurnstileValidateVO } from '@/types/api/common/captcha.ts'

/**
 * 获取验证码图片
 * GET /captcha/captchaImage
 */
export function getCaptchaImage(): Promise<ResponseType<CaptchaDTO>> {
  return request({
    url: '/captcha/captchaImage',
    method: 'get',
    headers: {
      skipToken: true,
    },
  })
}

/**
 * 验证 Cloudflare Turnstile 验证码
 * POST /captcha/turnstile/validate
 */
export function validateTurnstile(data: TurnstileValidateDTO): Promise<ResponseType<TurnstileValidateVO>> {
  return request({
    url: '/captcha/turnstile/validate',
    method: 'post',
    headers: {
      skipToken: true,
    },
    data,
  })
}

/**
 * 用户登录
 * POST /login
 */
export function login(data: UserLoginByUsernameDTO): Promise<ResponseType<UserLoginResponseDTO>> {
  return request({
    url: '/login',
    method: 'post',
    headers: {
      skipToken: true,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    data: new URLSearchParams(data as any).toString(),
  })
}

/**
 * 手机号登录
 * POST /login/phone
 */
export function loginByPhone(data: UserLoginByPhoneDTO): Promise<ResponseType<UserLoginResponseDTO>> {
  return request({
    url: '/login/phone',
    method: 'post',
    headers: {
      skipToken: true,
    },
    data,
  })
}

/**
 * 学号登录
 * POST /login/student
 */
export function loginByStudentNo(data: UserLoginByStudentNoDTO): Promise<ResponseType<UserLoginResponseDTO>> {
  return request({
    url: '/login/student',
    method: 'post',
    headers: {
      skipToken: true,
    },
    data,
  })
}

/**
 * 工号登录
 * POST /login/teacher
 */
export function loginByTeacherNo(data: UserLoginByTeacherNoDTO): Promise<ResponseType<UserLoginResponseDTO>> {
  return request({
    url: '/login/teacher',
    method: 'post',
    headers: {
      skipToken: true,
    },
    data,
  })
}

/**
 * 获取当前登录用户信息
 * GET /info
 */
export function getInfo(): Promise<ResponseType<AuthCurrentUserVO>> {
  return request({
    url: '/info',
    method: 'get',
  })
}

/**
 * 获取当前登录用户的路由列表（用于 Vue Router）
 * GET /routers
 */
export function getRouters(): Promise<ResponseType<RouterVO[]>> {
  return request({
    url: '/routers',
    method: 'get',
  })
}

/**
 * 获取当前登录用户的菜单树（用于 Ant Design Menu）
 * GET /menus
 * @param scene 应用场景: 'web'-日常应用, 'admin'-管理系统, 'mobile'-移动端, 'userInfo'-个人中心，默认为 'admin'
 */
export function getMenus(
  scene: 'web' | 'admin' | 'mobile' | 'userInfo' = 'admin'
): Promise<ResponseType<FunctionTreeVO[]>> {
  return request({
    url: '/menus',
    method: 'get',
    params: { scene },
  })
}

/**
 * 用户注册
 * POST /register
 */
export function register(data: UserRegisterByUsernameDTO): Promise<ResponseType<UserDetailVO>> {
  return request({
    url: '/register',
    method: 'post',
    headers: {
      skipToken: true,
    },
    data,
  })
}

/**
 * 用户退出登录
 * POST /logout
 */
export function logout(): Promise<ResponseType<Empty>> {
  return request({
    url: '/logout',
    method: 'post',
  })
}

/**
 * 忘记密码 - 发送短信验证码
 * POST /forgot-password/send-code
 */
export function forgotPasswordSendCode(data: ForgotPasswordSendCodeDTO): Promise<ResponseType<string>> {
  return request({
    url: '/forgot-password/send-code',
    method: 'post',
    headers: {
      skipToken: true,
    },
    data,
  })
}

/**
 * 忘记密码 - 重置密码
 * POST /forgot-password/reset
 */
export function forgotPasswordReset(data: ForgotPasswordResetDTO): Promise<ResponseType<Empty>> {
  return request({
    url: '/forgot-password/reset',
    method: 'post',
    headers: {
      skipToken: true,
    },
    data,
  })
}
