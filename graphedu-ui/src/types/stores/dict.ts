/**
 * 字典项类型
 */
export interface DictItem {
  /** 显示标签 */
  label: string
  /** 实际值 */
  value: string
  /** 标签类型（primary, success, warning, danger, default） */
  tagType?: string
  /** 自定义样式类 */
  cssClass?: string
  /** 图标（Ant Design Vue图标名称） */
  icon?: string
  /** 是否带边框（0否 1是） */
  bordered?: string
  /** 样式属性（JSONB格式） */
  style?: Record<string, any>
  /** 是否禁用 */
  disabled?: boolean
}

/**
 * 字典缓存项
 */
export interface DictCacheItem {
  /** 字典类型键 */
  key: string
  /** 字典数据列表 */
  value: DictItem[]
}

/**
 * 字典 Store 状态
 */
export interface DictState {
  /** 字典缓存列表 */
  dict: DictCacheItem[]
}
