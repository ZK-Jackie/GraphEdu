/**
 * 验证码响应类型
 */
export interface CaptchaDTO {
  /** 会话 ID */
  uuid: string
  /** 验证码图片的 base64 编码 */
  img: string
  /** 验证码答案，仅用于测试环境 */
  code?: string | number
  /** 是否启用验证码 */
  captchaEnabled?: boolean
}

/**
 * Cloudflare Turnstile 验证请求类型
 */
export interface TurnstileValidateDTO {
  /** Turnstile 验证 token（用户端返回的 response token） */
  token: string
  /** 用户 IP 地址（可选） */
  remoteIp?: string
}

/**
 * Cloudflare Turnstile 验证结果响应类型
 */
export interface TurnstileValidateVO {
  /** 验证是否成功 */
  success: boolean
  /** 验证时间戳（ISO 8601 格式） */
  challengeTs?: string
  /** 验证时使用的主机名 */
  hostname?: string
  /** 错误码列表 */
  errorCodes?: string[] | null
  /** 验证操作类型（仅 Managed 模式） */
  action?: string | null
  /** 客户数据（仅 Managed 模式） */
  cdata?: string | null
}
