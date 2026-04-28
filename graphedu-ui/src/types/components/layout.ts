/**
 * 布局节点类型定义
 * 用于 Golden Layout 多面板布局系统
 */

export interface PanelNode {
  type: 'panel'
  id: string
  tabs: any[]
  activeTab?: string
}

export interface SplitNode {
  type: 'split'
  id: string
  direction: 'horizontal' | 'vertical'
  ratio: number
  first: LayoutNode
  second: LayoutNode
}

export type LayoutNode = PanelNode | SplitNode
