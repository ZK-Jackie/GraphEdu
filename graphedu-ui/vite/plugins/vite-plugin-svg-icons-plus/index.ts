/**
 * 零依赖 SVG Icons 插件
 * 纯原生实现，无任何外部依赖
 */
import type { Plugin } from 'vite'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, relative, normalize, extname } from 'node:path'

interface Options {
  /** SVG 图标目录 */
  iconDirs: string[]
  /** dir 分隔符，默认为 '-' */
  dirSeparator?: string
  /** Symbol ID 模板，必须包含 [name]，可选 [dir] */
  symbolId?: string
  /** 是否优化 SVG（移除注释、空格等） */
  optimize?: boolean
  /** 自定义 DOM ID */
  domId?: string
  /** 注入位置 */
  inject?: 'body-first' | 'body-last'
}

interface IconData {
  content: string
  symbolId: string
  mtimeMs: number
}

const MODULE_ID_REGISTER = 'virtual:svg-icons-register'
const MODULE_ID_CLIENT = 'virtual:svg-icons-client'

export function createSvgIconsPlugin(options: Options): Plugin {
  const {
    iconDirs,
    dirSeparator = '-',
    symbolId = 'icon-[dir]-[name]',
    optimize = true,
    domId = '__svg_icons_dom__',
    inject = 'body-last',
  } = options

  if (!symbolId.includes('[name]')) {
    throw new Error('symbolId must contain [name]')
  }

  const cache = new Map<string, IconData>()

  return {
    name: 'vite:svg-icons-native',

    resolveId(id) {
      if (id === MODULE_ID_REGISTER || id === MODULE_ID_CLIENT) {
        return `\0${id}`
      }
      return null
    },

    load(id) {
      // 开发模式下也处理虚拟模块
      if (id === `\0${MODULE_ID_REGISTER}`) {
        return generateRegisterCode(iconDirs, cache, { symbolId, dirSeparator, optimize, domId, inject })
      }
      if (id === `\0${MODULE_ID_CLIENT}`) {
        return generateClientCode(cache)
      }
      return null
    },

    configureServer(server) {
      return () => {
        server.middlewares.use((req, res, next) => {
          const url = req.url!

          // 匹配虚拟模块 ID（支持带 \0 前缀的格式）
          if (url.includes(MODULE_ID_REGISTER)) {
            res.setHeader('Content-Type', 'application/javascript')
            res.setHeader('Cache-Control', 'no-cache')
            res.end(generateRegisterCode(iconDirs, cache, { symbolId, dirSeparator, optimize, domId, inject }))
          } else if (url.includes(MODULE_ID_CLIENT)) {
            res.setHeader('Content-Type', 'application/javascript')
            res.setHeader('Cache-Control', 'no-cache')
            res.end(generateClientCode(cache))
          } else {
            next()
          }
        })
      }
    },
  }
}

/**
 * 扫描并收集所有 SVG 文件
 */
function collectIcons(
  dirs: string[],
  cache: Map<string, IconData>,
  options: { symbolId: string; dirSeparator: string; optimize: boolean }
) {
  const symbols: string[] = []
  const ids: string[] = []

  for (const iconDir of dirs) {
    const svgs = walkDir(iconDir)

    for (const filePath of svgs) {
      const stats = statSync(filePath)
      const cached = cache.get(filePath)

      // 检查缓存
      if (cached?.mtimeMs === stats.mtimeMs) {
        symbols.push(cached.content)
        ids.push(cached.symbolId)
        continue
      }

      // 读取并处理 SVG
      let content = readFileSync(filePath, 'utf-8')

      // 优化 SVG
      if (options.optimize) {
        content = optimizeSvg(content)
      }

      // 生成 Symbol
      const relPath = relative(iconDir, filePath)
      const symbolId = generateSymbolId(relPath, options.symbolId, options.dirSeparator)
      const symbolContent = createSymbol(content, symbolId)

      // 更新缓存
      cache.set(filePath, {
        content: symbolContent,
        symbolId,
        mtimeMs: stats.mtimeMs,
      })

      symbols.push(symbolContent)
      ids.push(symbolId)
    }
  }
  return { symbols, ids }
}

/**
 * 递归遍历目录获取所有 SVG 文件
 */
function walkDir(dir: string): string[] {
  const files: string[] = []

  try {
    const entries = readdirSync(dir, { withFileTypes: true })

    for (const entry of entries) {
      const fullPath = join(dir, entry.name)

      if (entry.isDirectory()) {
        files.push(...walkDir(fullPath))
      } else if (entry.isFile() && entry.name.toLowerCase().endsWith('.svg')) {
        files.push(fullPath)
      }
    }
  } catch (_e) {
    // 目录不存在或无权限，忽略
  }

  return files
}

/**
 * 生成 Symbol ID
 * @param filePath 相对于 iconDirs 的文件路径
 * @param template Symbol ID 模板，支持 [dir] 和 [name] 占位符
 * @param dirSeparator 目录层级之间的分隔符
 */
function generateSymbolId(filePath: string, template: string, dirSeparator: string): string {
  // 标准化路径，统一使用 /
  const normalized = normalize(filePath).replace(/\\/g, '/')

  // 拆分路径
  const parts = normalized.split('/')
  const fileName = parts[parts.length - 1] ?? ''

  // 提取目录部分（不含文件名）
  const dirParts = parts.slice(0, -1)

  // 生成目录字符串（使用自定义分隔符连接）
  const dirStr = dirParts.length > 0 ? dirParts.join(dirSeparator) : ''

  // 移除文件扩展名
  const nameWithoutExt = fileName.replace(extname(fileName), '')

  // 替换模板占位符
  let id = template

  // 智能替换 [dir]
  if (id.includes('[dir]')) {
    if (dirStr) {
      // 有目录：直接替换
      id = id.replace('[dir]', dirStr)
    } else {
      // 无目录：移除 [dir] 及相邻的分隔符
      // 支持的模式：icon-[dir]-[name], icon-[dir][name], [dir]-icon, [dir]icon 等
      id = id
        .replace(/-\[dir\]-/g, '-') // icon-[dir]-[name] → icon-[name]
        .replace(/-\[dir\]/g, '') // icon-[dir] → icon
        .replace(/\[dir\]-/g, '') // [dir]-icon → icon
        .replace(/\[dir\]/g, '') // icon[dir] → icon
    }
  }

  // 替换 [name]
  id = id.replace('[name]', nameWithoutExt)

  return id
}

/**
 * 创建 <symbol> 元素
 */
function createSymbol(svgContent: string, id: string): string {
  // 提取 viewBox、width、height 等 SVG 属性
  const viewBoxMatch = svgContent.match(/viewBox=["']([^"']+)["']/)
  const viewBox = viewBoxMatch ? `viewBox="${viewBoxMatch[1]}"` : ''

  // 移除 <svg> 标签，保留内部内容
  const innerContent = svgContent
    .replace(/<svg[^>]*>/i, '')
    .replace(/<\/svg>/i, '')
    .trim()

  return `<symbol id="${id}" ${viewBox}>${innerContent}</symbol>`
}

/**
 * 优化 SVG（移除注释、多余空格等）
 */
function optimizeSvg(svg: string): string {
  return (
    svg
      // 移除 XML 声明
      .replace(/<\?xml[^?]*\?>/g, '')
      // 移除注释
      .replace(/<!--[\s\S]*?-->/g, '')
      // 移除 DOCTYPE
      .replace(/<!DOCTYPE[^>]*>/g, '')
      // 合并多个空格
      .replace(/\s+/g, ' ')
      // 移除标签间空格
      .replace(/>\s+</g, '><')
      // 替换固定颜色为 currentColor
      .replace(/stroke=["']#[0-9a-fA-F]{3,6}["']/g, 'stroke="currentColor"')
      .replace(/fill=["']#[0-9a-fA-F]{3,6}["']/gi, 'fill="currentColor"')
      .trim()
  )
}

/**
 * 生成注册模块代码
 */
function generateRegisterCode(
  dirs: string[],
  cache: Map<string, IconData>,
  options: {
    symbolId: string
    dirSeparator: string
    optimize: boolean
    domId: string
    inject: 'body-first' | 'body-last'
  }
): string {
  const { symbols } = collectIcons(dirs, cache, options)
  const symbolsHtml = symbols.join('\n')

  return `
    if (typeof window !== 'undefined') {
      (function() {
        const domId = '${options.domId}';
        let svgContainer = document.getElementById(domId);

        if (!svgContainer) {
          svgContainer = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
          svgContainer.id = domId;
          svgContainer.style.position = 'absolute';
          svgContainer.style.width = '0';
          svgContainer.style.height = '0';
          svgContainer.setAttribute('aria-hidden', 'true');
        }

        svgContainer.innerHTML = ${JSON.stringify(symbolsHtml)};
        ${getInjectCode(options.inject)}
      })();
    }
    export default {};
  `
}

/**
 * 生成客户端模块代码
 */
function generateClientCode(cache: Map<string, IconData>): string {
  const ids = Array.from(cache.values()).map((item) => item.symbolId)
  return `export default ${JSON.stringify(ids)}`
}

/**
 * 获取注入位置代码
 */
function getInjectCode(inject: 'body-first' | 'body-last'): string {
  if (inject === 'body-first') {
    return 'document.body.insertBefore(svgContainer, document.body.firstChild);'
  }
  return 'document.body.appendChild(svgContainer);'
}
