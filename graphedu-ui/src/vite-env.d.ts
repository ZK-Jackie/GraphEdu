/// <reference types="vite/client" />

declare module 'virtual:svg-icons-client' {
  const allIconIds: string[]
  export default allIconIds
}

interface ViteTypeOptions {
  strictImportMetaEnv: unknown
}

interface ImportMetaEnv {
  // 基础路径
  readonly VITE_APP_BASE_URL: string
  // 应用标题
  readonly VITE_APP_TITLE: string
  // 接口基础路径
  readonly VITE_API_BASE_URL: string
  // 接口超时时间，单位：毫秒
  readonly VITE_API_TIMEOUT: string
  // 接口请求间隔时间，单位：毫秒，超过此时间视为非重复提交
  readonly VITE_API_REQUEST_INTERVAL: string
  // 接口触发请求间隔检测的数据大小限制，单位：字节，超过此大小不进行重复提交检测
  readonly VITE_API_REQUEST_INTERVAL_DATA_THRESHOLD: string
  // 构建时是否生成压缩文件，可多选 'gzip' | 'brotli'，用英文逗号分隔
  readonly VITE_BUILD_COMPRESS: string
  // 是否开启二维码登录，true | false
  readonly VITE_LOGIN_QRCODE: string
  // 备案信息
  readonly VITE_ICP_LICENSE: string
  readonly VITE_PSA_LICENSE: string
  // Mock 模式开关
  readonly VITE_MOCK_ENABLED: string

  // Git 信息（构建时由插件注入）
  readonly VITE_GIT_REMOTE_URL: string
  readonly VITE_GIT_COMMIT_HASH: string
  readonly VITE_GIT_COMMIT_HASH_LONG: string
  readonly VITE_GIT_BRANCH: string
  readonly VITE_GIT_COMMIT_DATE: string
  readonly VITE_GIT_COMMIT_TIMESTAMP: number
  readonly VITE_GIT_TAG: string
  readonly VITE_GIT_COMMITTER_NAME: string
  readonly VITE_GIT_COMMITTER_EMAIL: string
  readonly VITE_GIT_COMMIT_MESSAGE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

interface PassedImportMetaEnv extends ImportMetaEnv {
  readonly VITE_API_TIMEOUT: number
  readonly VITE_API_REQUEST_INTERVAL: number
  readonly VITE_API_REQUEST_INTERVAL_DATA_THRESHOLD: number
  readonly VITE_BUILD_COMPRESS: string[]
  readonly VITE_LOGIN_QRCODE: boolean
}

interface AppMetaInfo {
  repository: string
  version: string
  lastUpdateTime: string
}
