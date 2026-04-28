export const LocalDarkModeKey = 'GRAPHEDU_DARK_MODE'
export const LocalLocaleKey = 'GRAPHEDU_LOCALE'
export const LocalTimeConfigKey = 'GRAPHEDU_TIME_CONFIG'
export const LocalVglLayoutKey = 'GRAPHEDU_VGL_LAYOUT'

export const SessionRequestObjectKey = 'GRAPHEDU_REQUEST_OBJECT'

export const CookieSidebarStatusKey = 'Sidebar-Status'
export const CookieAdminTokenKey = 'Admin-Token'

export const ViteEnv = {
  VITE_APP_TITLE: import.meta.env.VITE_APP_TITLE,
  VITE_APP_BASE_URL: import.meta.env.VITE_APP_BASE_URL,
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  VITE_API_TIMEOUT: Number(import.meta.env.VITE_API_TIMEOUT),
  VITE_API_REQUEST_INTERVAL: Number(import.meta.env.VITE_API_REQUEST_INTERVAL),
  VITE_API_REQUEST_INTERVAL_DATA_THRESHOLD: Number(import.meta.env.VITE_API_REQUEST_INTERVAL_DATA_THRESHOLD),
  VITE_BUILD_COMPRESS: import.meta.env.VITE_BUILD_COMPRESS
    ? import.meta.env.VITE_BUILD_COMPRESS.split(',').map((item) => item.trim())
    : [],
  VITE_LOGIN_QRCODE: import.meta.env.VITE_LOGIN_QRCODE === 'true',
  VITE_ICP_LICENSE: import.meta.env.VITE_ICP_LICENSE,
  VITE_PSA_LICENSE: import.meta.env.VITE_PSA_LICENSE,

  VITE_GIT_REMOTE_URL: import.meta.env.VITE_GIT_REMOTE_URL,
  VITE_GIT_COMMIT_HASH: import.meta.env.VITE_GIT_COMMIT_HASH,
  VITE_GIT_COMMIT_HASH_LONG: import.meta.env.VITE_GIT_COMMIT_HASH_LONG,
  VITE_GIT_BRANCH: import.meta.env.VITE_GIT_BRANCH,
  VITE_GIT_COMMIT_DATE: import.meta.env.VITE_GIT_COMMIT_DATE,
  VITE_GIT_COMMIT_TIMESTAMP: Number(import.meta.env.VITE_GIT_COMMIT_TIMESTAMP),
  VITE_GIT_TAG: import.meta.env.VITE_GIT_TAG,
  VITE_GIT_COMMITTER_NAME: import.meta.env.VITE_GIT_COMMITTER_NAME,
  VITE_GIT_COMMITTER_EMAIL: import.meta.env.VITE_GIT_COMMITTER_EMAIL,
  VITE_GIT_COMMIT_MESSAGE: import.meta.env.VITE_GIT_COMMIT_MESSAGE,
}
