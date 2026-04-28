import { execSync } from 'node:child_process'
import type { PluginOption } from 'vite'

/**
 * Git 信息接口
 */
export interface Index {
  /** 仓库远程地址 */
  remoteUrl: string
  /** 当前 commit hash（短格式） */
  commitHash: string
  /** 当前 commit hash（完整格式） */
  commitHashLong: string
  /** 当前分支名 */
  branch: string
  /** 最后一次提交时间（ISO 格式） */
  commitDate: string
  /** 最后一次提交时间戳 */
  commitTimestamp: number
  /** 当前 tag（如果存在） */
  tag: string
  /** 提交者姓名 */
  committerName: string
  /** 提交者邮箱 */
  committerEmail: string
  /** 提交消息 */
  commitMessage: string
  /** 自定义字段 */
  [key: string]: string | number
}

/**
 * 插件配置选项
 */
export interface GitInfoPluginOptions {
  /** Git 远程仓库名称，默认 'origin' */
  remoteName?: string
  /** 短 hash 长度，默认 7 */
  shortHashLength?: number
  /** 环境变量前缀，默认 'VITE_GIT_' */
  envPrefix?: string
  /** 是否包含分支信息，默认 true */
  includeBranch?: boolean
  /** 是否包含 tag，默认 true */
  includeTag?: boolean
  /** 是否包含提交者信息，默认 true */
  includeCommitter?: boolean
  /** 是否包含提交消息，默认 true */
  includeCommitMessage?: boolean
  /** 失败时的回退值 */
  fallbackValues?: Partial<Index>
  /** 自定义字段：{ 环境变量后缀: git命令 } */
  customFields?: Record<string, string>
  /** Git 命令执行选项 */
  execOptions?: {
    /** 工作目录，默认 process.cwd() */
    cwd?: string
    /** 环境变量 */
    env?: NodeJS.ProcessEnv
    /** 超时时间（毫秒） */
    timeout?: number
  }
  /** 是否启用插件，默认 true */
  enabled?: boolean
  /** 是否在失败时抛出错误，默认 false（静默失败） */
  throwOnError?: boolean
}

/**
 * 默认配置
 */
const defaultOptions: Required<Omit<GitInfoPluginOptions, 'fallbackValues' | 'customFields'>> = {
  remoteName: 'origin',
  shortHashLength: 7,
  envPrefix: 'VITE_GIT_',
  includeBranch: true,
  includeTag: true,
  includeCommitter: true,
  includeCommitMessage: true,
  execOptions: {
    cwd: process.cwd(),
    timeout: 5000,
  },
  enabled: true,
  throwOnError: false,
}

/**
 * 执行 git 命令并返回结果
 *
 * 支持的操作系统：
 * - Linux
 * - macOS
 * - Windows (cmd.exe, PowerShell, Git Bash)
 *
 * @param command Git 命令（不包含 `git` 前缀和错误重定向）
 * @param options 插件配置选项
 * @param defaultValue 失败时的默认值
 * @returns 命令执行结果
 */
function execGitCommand(command: string, options: GitInfoPluginOptions, defaultValue = ''): string {
  const opts = { ...defaultOptions.execOptions, ...options.execOptions }

  try {
    // 使用 stdio: 'pipe' 和 windowsHide: true 确保跨平台兼容
    // 错误输出会被自动捕获，不需要 shell 重定向
    const result = execSync(command, {
      encoding: 'utf-8',
      cwd: opts.cwd,
      env: opts.env,
      timeout: opts.timeout,
      stdio: ['ignore', 'pipe', 'ignore'], // 忽略 stdin 和 stderr，只捕获 stdout
      windowsHide: true, // Windows 隐藏子进程窗口
      shell: process.env.ComSpec, // 使用 shell 执行以支持 git 命令
    })
    return result.trim()
  } catch (error) {
    if (options.throwOnError) {
      throw new Error(`Git command failed: ${command}\n${error}`)
    }
    return defaultValue
  }
}

/**
 * 获取 Git 信息
 */
function getGitInfo(options: GitInfoPluginOptions): Index {
  const remoteName = options.remoteName ?? defaultOptions.remoteName
  const hashLength = options.shortHashLength ?? defaultOptions.shortHashLength

  // 获取远程地址
  const remoteUrl =
    (execGitCommand(`git remote get-url ${remoteName}`, options) || options.fallbackValues?.remoteUrl) ?? ''

  // 获取当前 commit hash
  const commitHashLong = (execGitCommand('git rev-parse HEAD', options) || options.fallbackValues?.commitHashLong) ?? ''
  const commitHash = commitHashLong
    ? commitHashLong.substring(0, hashLength)
    : (options.fallbackValues?.commitHash ?? '')

  // 获取当前分支
  const branch =
    options.includeBranch !== false
      ? ((execGitCommand('git rev-parse --abbrev-ref HEAD', options) || options.fallbackValues?.branch) ?? '')
      : ''

  // 获取最后一次提交时间（ISO 格式）
  const commitDate = (execGitCommand('git log -1 --format=%cI', options) || options.fallbackValues?.commitDate) ?? ''

  // 获取最后一次提交时间戳
  const commitTimestampStr =
    execGitCommand('git log -1 --format=%ct', options) || String(options.fallbackValues?.commitTimestamp ?? '0')
  const commitTimestamp = parseInt(commitTimestampStr, 10) || 0

  // 获取当前 tag
  const tag =
    options.includeTag !== false
      ? ((execGitCommand('git describe --tags --exact-match', options) || options.fallbackValues?.tag) ?? '')
      : ''

  // 获取提交者信息
  const committerName =
    options.includeCommitter !== false
      ? ((execGitCommand('git log -1 --format=%cn', options) || options.fallbackValues?.committerName) ?? '')
      : ''

  const committerEmail =
    options.includeCommitter !== false
      ? ((execGitCommand('git log -1 --format=%ce', options) || options.fallbackValues?.committerEmail) ?? '')
      : ''

  // 获取提交消息
  const commitMessage =
    options.includeCommitMessage !== false
      ? ((execGitCommand('git log -1 --format=%s', options) || options.fallbackValues?.commitMessage) ?? '')
      : ''

  // 自定义字段
  const customFields: Record<string, string | number> = {}
  if (options.customFields) {
    for (const [key, command] of Object.entries(options.customFields)) {
      customFields[key] = execGitCommand(command, options)
    }
  }

  return {
    remoteUrl,
    commitHash,
    commitHashLong,
    branch,
    commitDate,
    commitTimestamp,
    tag,
    committerName,
    committerEmail,
    commitMessage,
    ...customFields,
  }
}

/**
 * 将驼峰命名转换为环境变量命名（SCREAMING_SNAKE_CASE）
 */
function toEnvKey(key: string): string {
  return key
    .replace(/([A-Z])/g, '_$1')
    .toUpperCase()
    .replace(/^_/, '')
}

/**
 * Vite 插件：注入 Git 信息
 *
 * @example
 * // 默认配置
 * createGitInfoPlugin()
 *
 * @example
 * // 自定义远程仓库名称
 * createGitInfoPlugin({ remoteName: 'upstream' })
 *
 * @example
 * // 添加自定义字段
 * createGitInfoPlugin({
 *   customFields: {
 *     'BUILD_NUMBER': 'git rev-list --count HEAD',
 *     'LAST_AUTHOR': 'git log -1 --format=%an'
 *   }
 * })
 */
export default function createGitInfoPlugin(options: GitInfoPluginOptions = {}): PluginOption {
  // 如果禁用插件，返回空配置
  if (options.enabled === false) {
    return {
      name: 'vite-plugin-git-info',
      config: () => ({}),
    }
  }

  const mergedOptions = { ...defaultOptions, ...options }
  const { envPrefix } = mergedOptions

  return {
    name: 'vite-plugin-git-info',
    config: () => {
      const gitInfo = getGitInfo(mergedOptions)

      // 构建定义对象
      const define: Record<string, string | number> = {}

      for (const [key, value] of Object.entries(gitInfo)) {
        const envKey = `${envPrefix}${toEnvKey(key)}`
        if (typeof value === 'number') {
          define[`import.meta.env.${envKey}`] = value
        } else {
          define[`import.meta.env.${envKey}`] = JSON.stringify(value)
        }
      }

      return { define }
    },
    configResolved(config) {
      // 在构建时输出 Git 信息（仅在开发模式）
      if (config.command === 'build' && mergedOptions.enabled !== false) {
        const gitInfo = getGitInfo(mergedOptions)
        config.logger.info(
          `\n[collapse=Git Info]` +
            `\n  Remote: ${gitInfo.remoteUrl || 'N/A'}` +
            `\n  Branch: ${gitInfo.branch || 'N/A'}` +
            `\n  Commit: ${gitInfo.commitHash || 'N/A'}` +
            `\n  Tag: ${gitInfo.tag || 'N/A'}` +
            `\n  Date: ${gitInfo.commitDate || 'N/A'}` +
            `\n[/collapse]\n`
        )
      }
    },
  }
}
