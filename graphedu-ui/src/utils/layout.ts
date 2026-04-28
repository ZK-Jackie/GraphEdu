import type { LayoutNode, PanelNode, SplitNode } from '@/types/components/layout.ts'

/**
 * 布局操作工具类
 */
export class LayoutUtils {
  /**
   * 创建初始面板
   */
  static createInitialPanel(tabs: any[] = []): PanelNode {
    return {
      type: 'panel',
      id: `panel-${Date.now()}`,
      tabs,
      activeTab: tabs[0]?.path,
    }
  }

  /**
   * 水平分割面板
   */
  static splitHorizontal(sourcePanel: PanelNode, newTabs: any[] = []): SplitNode {
    return {
      type: 'split',
      direction: 'horizontal',
      ratio: 0.5,
      first: sourcePanel,
      second: this.createInitialPanel(newTabs),
      id: `split-${Date.now()}`,
    }
  }

  /**
   * 垂直分割面板
   */
  static splitVertical(sourcePanel: PanelNode, newTabs: any[] = []): SplitNode {
    return {
      type: 'split',
      direction: 'vertical',
      ratio: 0.5,
      first: sourcePanel,
      second: this.createInitialPanel(newTabs),
      id: `split-${Date.now()}`,
    }
  }

  /**
   * 查找面板
   */
  static findPanel(node: LayoutNode, panelId: string): PanelNode | null {
    if (node.type === 'panel') {
      return node.id === panelId ? node : null
    }

    const firstResult = this.findPanel(node.first, panelId)
    if (firstResult) return firstResult

    return this.findPanel(node.second, panelId)
  }

  /**
   * 查找父节点
   */
  static findParent(node: LayoutNode, targetId: string): SplitNode | null {
    if (node.type === 'split') {
      if (node.first.id === targetId || node.second.id === targetId) {
        return node
      }

      const parentInFirst = this.findParent(node.first, targetId)
      if (parentInFirst) return parentInFirst

      return this.findParent(node.second, targetId)
    }

    return null
  }

  /**
   * 移除面板并合并兄弟节点
   */
  static removePanel(node: LayoutNode, panelId: string): LayoutNode | null {
    if (node.type === 'panel') {
      return node.id === panelId ? null : node
    }

    const first = this.removePanel(node.first, panelId)
    const second = this.removePanel(node.second, panelId)

    if (!first) return second
    if (!second) return first

    return { ...node, first, second }
  }

  /**
   * 移动标签到另一个面板
   */
  static moveTab(node: LayoutNode, tabPath: string, fromPanelId: string, toPanelId: string): LayoutNode {
    const fromPanel = this.findPanel(node, fromPanelId)
    const toPanel = this.findPanel(node, toPanelId)

    if (!fromPanel || !toPanel) return node

    const tabToMove = fromPanel.tabs.find((t) => t.path === tabPath)
    if (!tabToMove) return node

    return {
      ...node,
      first: this._moveTabRecursive((node as SplitNode).first, tabToMove, fromPanelId, toPanelId),
      second: this._moveTabRecursive((node as SplitNode).second, tabToMove, fromPanelId, toPanelId),
    } as SplitNode
  }

  private static _moveTabRecursive(node: LayoutNode, tab: any, fromPanelId: string, toPanelId: string): LayoutNode {
    if (node.type === 'panel') {
      if (node.id === fromPanelId) {
        return {
          ...node,
          tabs: node.tabs.filter((t) => t.path !== tab.path),
          activeTab: node.activeTab === tab.path ? node.tabs.find((t) => t.path !== tab.path)?.path : node.activeTab,
        }
      }

      if (node.id === toPanelId) {
        return {
          ...node,
          tabs: [...node.tabs, tab],
          activeTab: tab.path,
        }
      }

      return node
    }

    return {
      ...node,
      first: this._moveTabRecursive(node.first, tab, fromPanelId, toPanelId),
      second: this._moveTabRecursive(node.second, tab, fromPanelId, toPanelId),
    }
  }

  /**
   * 更新分割比例
   */
  static updateRatio(node: LayoutNode, splitId: string, ratio: number): LayoutNode {
    if (node.type === 'split' && node.id === splitId) {
      return { ...node, ratio: Math.max(0.1, Math.min(0.9, ratio)) }
    }

    if (node.type === 'split') {
      return {
        ...node,
        first: this.updateRatio(node.first, splitId, ratio),
        second: this.updateRatio(node.second, splitId, ratio),
      }
    }

    return node
  }

  /**
   * 获取所有面板
   */
  static getAllPanels(node: LayoutNode): PanelNode[] {
    if (node.type === 'panel') {
      return [node]
    }

    return [...this.getAllPanels(node.first), ...this.getAllPanels(node.second)]
  }

  /**
   * 计算布局深度
   */
  static getDepth(node: LayoutNode): number {
    if (node.type === 'panel') {
      return 1
    }

    return 1 + Math.max(this.getDepth(node.first), this.getDepth(node.second))
  }
}
