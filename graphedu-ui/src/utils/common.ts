/**
 * 时间格式化
 * @param time 时间字符串 | 时间戳 | Date对象
 * @param pattern 格式化规则（可选）
 */
export function parseTime(time: string | number | Date | null | undefined, pattern?: string): string | null {
  if (time == null || time === '') {
    return null
  }
  const format = pattern ?? '{y}-{m}-{d} {h}:{i}:{s}'
  let date: Date
  if (typeof time === 'object') {
    date = time
  } else {
    if (typeof time === 'string' && /^[0-9]+$/.test(time)) {
      time = parseInt(time)
    } else if (typeof time === 'string') {
      // 处理 ISO 8601 格式（支持 Python 后端的 6 位微秒）
      // 例如：2024-01-01T12:00:00.123456 或 2024-01-01T12:00:00.123
      time = time
        .replace(new RegExp(/-/gm), '/')
        .replace('T', ' ')
        .replace(/\.[\d]+$/, '') // 移除小数点后的所有数字（毫秒/微秒）
    }
    if (typeof time === 'number' && time.toString().length === 10) {
      time = time * 1000
    }
    date = new Date(time)
  }
  type FormatKey = 'y' | 'm' | 'd' | 'h' | 'i' | 's' | 'a'
  const formatObj: Record<FormatKey, number> = {
    y: date.getFullYear(),
    m: date.getMonth() + 1,
    d: date.getDate(),
    h: date.getHours(),
    i: date.getMinutes(),
    s: date.getSeconds(),
    a: date.getDay(),
  }

  return format.replace(/{([ymdhisa])+}/g, (result, key: FormatKey): string => {
    const value: number = formatObj[key]
    // Note: getDay() returns 0 on Sunday
    if (key === 'a') {
      return ['日', '一', '二', '三', '四', '五', '六'][value] ?? ''
    }
    if (result.length > 0 && value < 10) {
      return '0' + value
    }
    return value.toString() || '0'
  })
}

/**
 * 格式化时间的便捷别名（等同于 parseTime）
 */
export const formatTime = parseTime

/**
 * 添加日期范围
 * @param params 范围参数
 * @param dateRange 日期范围（可选）
 * @param propName 参数名称后缀（可选）
 */
export function addDateRange(params: Record<string, any>, dateRange?: any[], propName?: string): Record<string, any> {
  const search = params
  const range = Array.isArray(dateRange) ? dateRange : []
  if (typeof propName === 'undefined') {
    search['beginTime'] = range[0]
    search['endTime'] = range[1]
  } else {
    search['begin' + propName] = range[0]
    search['end' + propName] = range[1]
  }
  return search
}

// 回显数据字典
export function selectDictLabel(datas: any[], value: any): string {
  if (value === undefined) {
    return ''
  }
  const actions: string[] = []
  datas.some((item) => {
    if (item.value === '' + value) {
      actions.push(item.label)
      return true
    }
    return false
  })
  if (actions.length === 0) {
    actions.push(value)
  }
  return actions.join('')
}

// 回显数据字典（字符串数组）
export function selectDictLabels(datas: any[], value?: any, separator?: string): string {
  if (value === undefined || value.length === 0) {
    return ''
  }
  let valueStr = value
  if (Array.isArray(value)) {
    valueStr = value.join(',')
  }
  const actions: string[] = []
  const currentSeparator = separator ?? ','
  const temp = valueStr.split(currentSeparator)
  for (let i = 0; i < temp.length; i++) {
    let match = false
    datas.some((item) => {
      if (item.value === '' + temp[i]) {
        actions.push(item.label + currentSeparator)
        match = true
        return true
      }
      return false
    })
    if (!match) {
      actions.push(temp[i] + currentSeparator)
    }
  }
  const result = actions.join('')
  return result.substring(0, result.length - 1)
}

// 字符串格式化(%s )
export function sprintf(str: string, ...args: any[]): string {
  let flag = true,
    i = 0
  str = str.replace(/%s/g, function () {
    const arg = args[i++]
    if (typeof arg === 'undefined') {
      flag = false
      return ''
    }
    return arg
  })
  return flag ? str : ''
}

// 转换字符串，undefined,null等转化为""
export function parseStrEmpty(str: any): string {
  if (!str || str === 'undefined' || str === 'null') {
    return ''
  }
  return str
}

// 数据合并
export function mergeRecursive(source: Record<string, any>, target: Record<string, any>): Record<string, any> {
  for (const p in target) {
    try {
      if (target[p].constructor === Object) {
        source[p] = mergeRecursive(source[p], target[p])
      } else {
        source[p] = target[p]
      }
    } catch (_e) {
      source[p] = target[p]
    }
  }
  return source
}

/**
 * 构造树型结构数据
 * @param data 数据源
 * @param id id字段 默认 'id'
 * @param parentId 父节点字段 默认 'parentId'
 * @param children 孩子节点字段 默认 'children'
 */
export function handleTree(data: any[], id?: string, parentId?: string, children?: string): any[] {
  const config = {
    id: id ?? 'id',
    parentId: parentId ?? 'parentId',
    childrenList: children ?? 'children',
  }

  const childrenListMap: Record<string, any[]> = {}
  const nodeIds: Record<string, any> = {}
  const tree: any[] = []

  for (const d of data) {
    const pid = d[config.parentId]
    childrenListMap[pid] ??= []
    nodeIds[d[config.id]] = d
    childrenListMap[pid].push(d)
  }

  for (const d of data) {
    const pid = d[config.parentId]
    if (nodeIds[pid] == null) {
      tree.push(d)
    }
  }

  for (const t of tree) {
    adaptToChildrenList(t)
  }

  function adaptToChildrenList(o: any): void {
    if (childrenListMap[o[config.id]] !== null) {
      o[config.childrenList] = childrenListMap[o[config.id]]
    }
    if (o[config.childrenList]) {
      for (const c of o[config.childrenList]) {
        adaptToChildrenList(c)
      }
    }
  }

  return tree
}

/**
 * 参数处理
 * @param params  参数
 */
export function transParams(params: Record<string, any>): string {
  let result = ''
  for (const propName of Object.keys(params)) {
    const value = params[propName]
    const part = encodeURIComponent(propName) + '='
    if (value !== null && value !== '' && typeof value !== 'undefined') {
      if (typeof value === 'object') {
        for (const key of Object.keys(value)) {
          if (value[key] !== null && value[key] !== '' && typeof value[key] !== 'undefined') {
            const paramName = propName + '[' + key + ']'
            const subPart = encodeURIComponent(paramName) + '='
            result += subPart + encodeURIComponent(value[key]) + '&'
          }
        }
      } else {
        result += part + encodeURIComponent(value) + '&'
      }
    }
  }
  return result
}

// 返回项目路径
export function getNormalPath(p: string): string {
  if (p.length === 0 || !p || p === 'undefined') {
    return p
  }
  const res = p.replace('//', '/')
  if (res[res.length - 1] === '/') {
    return res.slice(0, res.length - 1)
  }
  return res
}

// 验证是否为blob格式
export function blobValidate(data: { type: string }): boolean {
  return data.type !== 'application/json'
}
