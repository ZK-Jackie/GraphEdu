import useDictStore from '@/stores/modules/dict.ts'
import { getDictDataByType } from '@/api/system/dict.ts'
import type { DictItem } from '@/types/stores/dict.ts'
import type { DictType } from '@/types/api/system/dict.ts'

/**
 * 获取字典数据 composable
 * @param args 字典类型列表
 * @returns 字典数据对象
 *
 * @example
 * const { sys_normal_disable, sys_user_sex } = useDict('sys_normal_disable', 'sys_user_sex')
 */
export function useDict(...args: DictType[]) {
  const result: Record<DictType, Ref<DictItem[]>> = {}

  args.forEach((dictType) => {
    // 为每个字典类型创建独立的 Ref，确保响应式更新
    const dictRef = ref<DictItem[]>([])
    result[dictType] = dictRef

    // 先从缓存获取
    const dicts = useDictStore().getDict(dictType)
    if (dicts) {
      dictRef.value = dicts
    } else {
      // 缓存未命中，从后端获取
      getDictDataByType(dictType).then((resp) => {
        if (resp.data) {
          if (resp.data.length === 0) {
            console.warn("[useDict utils] 字典类型 '%s' 的数据为空数组", dictType)
          }
          const mapped = resp.data.map((p) => ({
            label: p.dictLabel,
            value: String(p.dictValue), // 确保类型为字符串
            tagType: p.color ?? 'default',
            style: p.style ?? {},
            icon: p.icon ?? '',
            bordered: p.bordered ?? 'N',
          }))
          dictRef.value = mapped // 直接更新 Ref，触发响应式
          useDictStore().setDict(dictType, mapped)
        }
      })
    }
  })

  return result
}

/**
 * 根据字典类型和值获取字典标签
 * @param dictType 字典类型
 * @param dictValue 字典值
 * @returns 字典标签，未找到则返回原值
 */
export function getDictLabel(dictType: string, dictValue: string): string {
  const dicts = useDictStore().getDict(dictType)
  if (!dicts) return dictValue

  const dict = dicts.find((d) => d.value === dictValue)
  return dict?.label ?? dictValue
}

/**
 * 根据字典类型和值获取字典标签类型
 * @param dictType 字典类型
 * @param dictValue 字典值
 * @returns 标签类型（primary, success, warning, danger, default）
 */
export function getDictTagType(dictType: string, dictValue: string): string {
  const dicts = useDictStore().getDict(dictType)
  if (!dicts) return 'default'

  const dict = dicts.find((d) => d.value === dictValue)
  return dict?.tagType ?? 'default'
}

/**
 * 根据字典类型获取所有字典数据
 * @param dictType 字典类型
 * @returns 字典数据数组
 */
export function getDictData(dictType: string): DictItem[] {
  const dicts = useDictStore().getDict(dictType)
  return dicts ?? []
}

/**
 * 根据字典类型和标签获取字典值
 * @param dictType 字典类型
 * @param dictLabel 字典标签
 * @returns 字典值，未找到则返回空字符串
 */
export function getDictValue(dictType: string, dictLabel: string): string {
  const dicts = useDictStore().getDict(dictType)
  if (!dicts) return ''

  const dict = dicts.find((d) => d.label === dictLabel)
  return dict?.value ?? ''
}

/**
 * 根据字典类型获取字典选项（用于下拉框等场景）
 * @param dictType 字典类型
 * @returns 字典数据数组（如果缓存不存在则异步加载）
 */
export async function getDictOptions(dictType: string): Promise<DictItem[]> {
  const cached = useDictStore().getDict(dictType)
  if (cached && cached.length > 0) {
    return cached
  }

  const resp = await getDictDataByType(dictType)
  if (resp.code === 200 && resp.data) {
    const options = resp.data.map((p) => ({
      label: p.dictLabel,
      value: String(p.dictValue),
      tagType: p.color ?? 'default',
      style: p.style ?? {},
      icon: p.icon ?? '',
      bordered: p.bordered ?? 'N',
    }))
    useDictStore().setDict(dictType, options)
    return options
  }

  return []
}

/**
 * 将字典值数组转换为标签数组
 * @param dictType 字典类型
 * @param values 字典值数组
 * @param separator 分隔符（当 values 为字符串时使用）
 * @returns 标签数组
 */
export function getDictLabels(dictType: string, values: string | string[], separator = ','): string[] {
  const dicts = useDictStore().getDict(dictType)
  if (!dicts) return []

  const valueArray = Array.isArray(values) ? values : values.split(separator)
  return valueArray.map((val) => {
    const dict = dicts.find((d) => d.value === val)
    return dict?.label ?? val
  })
}
