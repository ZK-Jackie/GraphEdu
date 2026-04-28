/**
 * 认证相关类型定义
 * 对应后端：graphedu/common/models/vo/auth.py
 */

import type { CSSProperties } from 'vue'

/**
 * 路由元信息（对应 Vue Router 的 meta 字段）
 */
export interface RouterMeta {
  /** 权限标识（唯一标识） */
  key?: string
  /** 页面标题 */
  title?: string
  /** 菜单图标 */
  icon?: string
  /** 是否缓存页面（对应 route_cache） */
  keepAlive?: boolean
  /** 是否固定在标签栏 */
  affix?: boolean
  /** 外链地址（当 route_external=1 时有效） */
  link?: string
  /** 是否隐藏（对应 visible=0） */
  hidden?: boolean
  /** 是否启用（对应 status=0） */
  enabled?: boolean
  /** 显示顺序（对应 sort_order） */
  order?: number
  /** 菜单CSS样式（JSON格式，使用css-in-js格式） */
  style?: CSSProperties
  /** 菜单选项样式（JSON格式） */
  optionStyle?: Record<string, boolean | string>
  /** 索引签名：允许任意字符串属性，兼容 Vue Router RouteMeta */
  [key: string]: any
}

/**
 * 路由信息 VO（对齐 Vue Router 的 RouteRecordRaw）
 */
export interface RouterVO {
  /** 路由路径 */
  path: string
  /** 路由名称 */
  name?: string
  /** 组件路径 */
  component?: string
  /** 重定向路径 */
  redirect?: string
  /** 路由别名 */
  alias?: string | string[]
  /** 传递给组件的 props */
  props?: boolean | Record<string, any>
  /** 路由 query 参数（对应 route_query） */
  query?: Record<string, any>
  /** 路由元信息 */
  meta?: RouterMeta
  /** 子路由列表 */
  children?: RouterVO[]
}
