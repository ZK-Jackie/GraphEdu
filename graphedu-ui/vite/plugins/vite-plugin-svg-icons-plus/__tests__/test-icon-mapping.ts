/**
 * SVG Icons 映射关系测试脚本
 * 运行: npx tsx scripts/test-icon-mapping.ts
 */

interface TestCase {
  path: string
  description: string
}

interface Config {
  name: string
  dirSeparator: string
  symbolId: string
}

// 模拟 generateSymbolId 函数（从插件中复制）
function generateSymbolId(filePath: string, template: string, dirSeparator: string): string {
  const normalized = filePath.replace(/\\/g, '/')
  const parts = normalized.split('/')
  const fileName = parts[parts.length - 1] ?? ''
  const dirParts = parts.slice(0, -1)
  const dirStr = dirParts.length > 0 ? dirParts.join(dirSeparator) : ''
  const nameWithoutExt = fileName.replace(/\.[^/.]+$/, '')

  let id = template

  if (id.includes('[dir]')) {
    if (dirStr) {
      id = id.replace('[dir]', dirStr)
    } else {
      id = id
        .replace(/-\[dir\]-/g, '-')
        .replace(/-\[dir\]/g, '')
        .replace(/\[dir\]-/g, '')
        .replace(/\[dir\]/g, '')
    }
  }

  id = id.replace('[name]', nameWithoutExt)
  return id
}

// 测试用例
const testCases: TestCase[] = [
  { path: 'common/home.svg', description: '单层目录' },
  { path: 'user-add.svg', description: '根目录，文件名含横线' },
  { path: 'system/settings/edit-confirm.svg', description: '多层目录+文件名含横线' },
  { path: 'navigation/home/default.svg', description: '三层目录' },
  { path: 'arrow-left-circle.svg', description: '根目录，文件名含多个横线' },
  { path: 'logo.svg', description: '根目录，简单文件名' },
  { path: 'actions/edit-confirm-success.svg', description: '单层目录+文件名含多个横线' },
]

// 配置方案
const configs: Config[] = [
  {
    name: '默认配置（推荐中型项目）',
    dirSeparator: '-',
    symbolId: 'icon-[dir]-[name]',
  },
  {
    name: '斜杠分隔（推荐大型项目）',
    dirSeparator: '/',
    symbolId: 'icon-[dir]/[name]',
  },
  {
    name: '扁平化（小型项目）',
    dirSeparator: '/',
    symbolId: '[name]',
  },
  {
    name: '紧凑风格',
    dirSeparator: '',
    symbolId: 'icon[dir][name]',
  },
]

// 运行测试
console.log('\n' + '='.repeat(100))
console.log('SVG Icons 映射关系测试')
console.log('='.repeat(100))

for (const config of configs) {
  console.log(`\n【${config.name}】`)
  console.log(`配置: dirSeparator="${config.dirSeparator}", symbolId="${config.symbolId}"`)
  console.log('-'.repeat(100))

  for (const testCase of testCases) {
    const id = generateSymbolId(testCase.path, config.symbolId, config.dirSeparator)
    console.log(`${testCase.path.padEnd(45)} → ${id.padEnd(45)} // ${testCase.description}`)
  }
}

// 验证冲突
console.log('\n' + '='.repeat(100))
console.log('冲突检测')
console.log('='.repeat(100))

const flatConfig: Config = {
  name: '扁平化',
  dirSeparator: '/',
  symbolId: '[name]',
}

const generatedIds = new Map<string, string[]>()

for (const testCase of testCases) {
  const id = generateSymbolId(testCase.path, flatConfig.symbolId, flatConfig.dirSeparator)

  if (!generatedIds.has(id)) {
    generatedIds.set(id, [])
  }
  generatedIds.get(id)!.push(testCase.path)
}

const conflicts: string[][] = []
generatedIds.forEach((paths, id) => {
  if (paths.length > 1) {
    conflicts.push([id, ...paths])
  }
})

if (conflicts.length > 0) {
  console.log('\n⚠️  检测到命名冲突（使用扁平化配置时）：\n')
  for (const conflict of conflicts) {
    const [id, ...paths] = conflict
    console.log(`  Symbol ID: ${id}`)
    paths.forEach((path: string) => {
      console.log(`    - ${path}`)
    })
    console.log()
  }
} else {
  console.log('\n✓ 当前测试用例无冲突\n')
}

console.log('='.repeat(100) + '\n')
