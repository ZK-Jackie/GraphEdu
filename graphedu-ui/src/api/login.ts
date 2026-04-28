import request from '@/utils/request'
import type { UserLoginByUsernameDTO, UserRegisterByUsernameDTO } from '@/types/api/system/user'
import type { AuthCurrentUserVO, UserLoginResponseDTO } from '@/types/api/system/user.ts'

import type { CaptchaDTO } from '@/types/api/common/captcha.ts'

// 登录方法
export function login(data: UserLoginByUsernameDTO): Promise<UserLoginResponseDTO> {
  return request({
    url: '/login',
    headers: {
      skipToken: true,
      skipRepeatSubmitCheck: false,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    method: 'post',
    data: data,
  })
}

// 获取用户详细信息
export function getInfo(): Promise<AuthCurrentUserVO> {
  return request({
    url: '/info',
    method: 'get',
  })
}

// 获取用户路由列表
export function getRouters() {
  console.warn('getRouters is deprecated, please use getInfo instead to get user info and routers')
  return request({
    url: '/routers',
    method: 'get',
  })
}

// 注册方法
export function register(data: UserRegisterByUsernameDTO) {
  return request({
    url: '/register',
    headers: {
      skipToken: true,
    },
    method: 'post',
    data: data,
  })
}

// 退出方法
export function logout(): Promise<null> {
  return request({
    url: '/logout',
    method: 'post',
  })
}

// 获取验证码
export function getCodeImg(): Promise<CaptchaDTO> {
  return request({
    url: '/captchaImage',
    headers: {
      skipToken: true,
    },
    method: 'get',
    timeout: 20000,
  })
}
