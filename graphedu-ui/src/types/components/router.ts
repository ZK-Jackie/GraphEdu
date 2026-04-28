// 后端传入的路由树节点类型 / 用于生成 Ant Design 菜单的数据结构 / 用于生成 Vue Router 路由的数据结构
export type { RouterMeta } from '@/types/api/common/auth.ts'
import type { RouterMeta } from '@/types/api/common/auth.ts'

export interface RouterTreeItem {
  // 唯一标识，一般为 id 或 权限标识
  key: string
  // 显示标题
  title: string
  // 显示类型
  type: 'group' | 'divider' | 'item' | 'menu'
  // 图标（当类型为 `item` 或 `menu` 时有效）
  icon?: string
  // 路由名称（当类型为 `item` 或 `menu` 时有效）
  name?: string
  // 子节点（当类型为 `group` 或 `menu` 时有效，其余时候为空数组或 null 值）
  children?: Array<RouterTreeItem>
  // 显示状态（当类型为 `item` 或 `menu` 时有效）
  status?: DividerStyle
}

export interface DividerStyle extends RouterTreeItemStatus {
  // 是否虚线
  dashed: boolean
}

// 路由树节点显示状态类型
export interface RouterTreeItemStatus {
  // 是否显示
  visible: boolean
  // 是否禁用
  disabled: boolean
  // 样式
  style?: string
}

export interface BaseRouter {
  // 路由名称（程序用）
  name: string
  // 路由路径（程序用）
  path?: string
  // query 参数（程序用）
  query?: Record<string, any>
  // 路由参数（程序用）
  params?: Record<string, any>
  // 路由元信息（用户展示用）
  meta?: RouterMeta
}
