<script setup lang="ts">
/**
 * NvlGraph - 基于 @neo4j-nvl/base 的知识图谱 Vue 3 封装
 *
 * 场景：
 *  - mode="view"  (Phase 5) 只读浏览：力导向布局、悬浮 Tooltip、节点导航
 *  - mode="edit"  (Phase 4) 审核编辑：可拖拽节点、低置信度关系标记
 *
 * 依赖：
 *  - @neo4j-nvl/base ^1.1.0
 *  - @neo4j-nvl/interaction-handlers ^1.1.0
 */
import NVL from '@neo4j-nvl/base'
import type { HitTargets, NvlOptions, Node as NvlBaseNode, Relationship as NvlBaseRel } from '@neo4j-nvl/base'
import {
  ClickInteraction,
  DragNodeInteraction,
  HoverInteraction,
  PanInteraction,
  ZoomInteraction,
} from '@neo4j-nvl/interaction-handlers'
import type { GraphMode, NvlNode, NvlRel, TooltipInfo } from './types'
import { useNvlStyles } from './useNvlStyles'

// ─── Props / Emits ───────────────────────────────────────────────────────────

interface Props {
  /** 图谱节点数组 */
  nodes: NvlNode[]
  /** 图谱关系数组 */
  rels: NvlRel[]
  /** 工作模式：view（只读浏览）/ edit（审核编辑） */
  mode?: GraphMode
  /** 布局算法 */
  layout?: 'forceDirected' | 'hierarchical' | 'grid' | 'circular'
  /** 受控高亮节点 ID 列表（外部驱动选中状态） */
  selectedNodeIds?: string[]
  /** 是否显示加载遮罩 */
  loading?: boolean
  /** 初始缩放级别，默认 0.8 */
  initialZoom?: number
  /** 是否在布局稳定后自动 fit，默认 true */
  fitOnLayout?: boolean
}

interface Emits {
  /** 节点被点击 */
  (e: 'node-click', node: NvlNode, event: MouseEvent): void

  /** 节点悬浮状态变化（null = 离开） */
  (e: 'node-hover', info: TooltipInfo | null): void

  /** 关系被点击 */
  (e: 'rel-click', rel: NvlRel, event: MouseEvent): void

  /** 点击空白画布 */
  (e: 'canvas-click', event: MouseEvent): void

  /** 节点拖拽结束（含新坐标） */
  (e: 'node-drag-end', nodes: NvlNode[]): void

  /** 布局计算完成 */
  (e: 'layout-done'): void
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'view',
  layout: 'forceDirected',
  selectedNodeIds: () => [],
  loading: false,
  initialZoom: 0.8,
  fitOnLayout: true,
})
const emit = defineEmits<Emits>()

// ─── 内部状态 ─────────────────────────────────────────────────────────────────

const containerRef = ref<HTMLDivElement | null>(null)

/** NVL 实例 */
let nvl: NVL | null = null

/** 当前注册的 interaction handlers（便于销毁） */
let interactions: Array<{
  destroy: () => void
}> = []

/** ResizeObserver，监听容器大小变化 */
let resizeObserver: ResizeObserver | null = null

/** 当前悬浮的节点 ID（用于去重触发 hover emit） */
let hoveredNodeId: string | null = null

const { styleNodes, styleRels } = useNvlStyles()

// ─── 工具函数 ─────────────────────────────────────────────────────────────────

/** 销毁所有 interaction handlers */
function destroyInteractions(): void {
  interactions.forEach((h) => h.destroy())
  interactions = []
}

/** 根据当前 mode 注册 interaction handlers */
function registerInteractions(): void {
  if (!nvl) return
  destroyInteractions()

  const isEditMode = props.mode === 'edit'

  // 缩放和平移 - 两种模式均需要
  const zoom = new ZoomInteraction(nvl)
  const pan = new PanInteraction(nvl)
  interactions.push(zoom, pan)

  // 点击交互（selectOnClick 在两种模式均开启）
  const click = new ClickInteraction(nvl, { selectOnClick: true })
  click.updateCallback('onNodeClick', (node: NvlBaseNode, _hits: HitTargets, evt: MouseEvent) => {
    emit('node-click', node as NvlNode, evt)
  })
  click.updateCallback('onRelationshipClick', (rel: NvlBaseRel, _hits: HitTargets, evt: MouseEvent) => {
    emit('rel-click', rel as NvlRel, evt)
  })
  click.updateCallback('onCanvasClick', (evt: MouseEvent) => {
    nvl?.deselectAll()
    emit('canvas-click', evt)
  })
  interactions.push(click)

  // 悬浮高亮 - 两种模式均开启，view 模式额外处理 Tooltip emit
  const hover = new HoverInteraction(nvl, { drawShadowOnHover: true })
  hover.updateCallback(
    'onHover',
    (element: NvlBaseNode | NvlBaseRel | null | undefined, _hits: HitTargets, evt: MouseEvent) => {
      // NVL 在某些边界场景可能传入空值，先做保护，避免 `in` 运算符触发 TypeError。
      if (!element || typeof element !== 'object') {
        hoveredNodeId = null
        emit('node-hover', null)
        return
      }

      // 只处理节点悬浮（关系悬浮不显示 Tooltip）。
      if ('from' in element) {
        hoveredNodeId = null
        emit('node-hover', null)
        return
      }

      const node = element as NvlNode
      if (node.id !== hoveredNodeId) {
        hoveredNodeId = node.id
        emit('node-hover', { node, x: evt.clientX, y: evt.clientY })
      }
    }
  )
  interactions.push(hover)

  // 拖拽节点 - 仅 edit 模式
  if (isEditMode) {
    const drag = new DragNodeInteraction(nvl)
    drag.updateCallback('onDragEnd', (nodes: NvlBaseNode[], evt: MouseEvent) => {
      emit('node-drag-end', nodes as NvlNode[])
    })
    interactions.push(drag)
  }
}

// ─── NVL 初始化 ───────────────────────────────────────────────────────────────

function initNvl(): void {
  if (!containerRef.value) return

  const styledNodes = styleNodes(props.nodes)
  const styledRels = styleRels(props.rels)

  const options: NvlOptions = {
    layout: props.layout,
    renderer: 'canvas', // canvas 支持 captions 文字渲染
    initialZoom: props.initialZoom,
    disableTelemetry: true,
    callbacks: {
      onLayoutDone: () => {
        if (props.fitOnLayout) {
          nvl?.fit(
            props.nodes.map((n) => n.id),
            { animated: true }
          )
        }
        emit('layout-done')
      },
    },
  }

  nvl = new NVL(containerRef.value, styledNodes, styledRels, options)
  registerInteractions()
}

/** 完全销毁 NVL 实例和所有资源 */
function destroyNvl(): void {
  destroyInteractions()
  resizeObserver?.disconnect()
  resizeObserver = null
  nvl?.destroy()
  nvl = null
  hoveredNodeId = null
}

// ─── 数据增量更新 ─────────────────────────────────────────────────────────────

/**
 * 将新 nodes/rels 与当前图谱做增量同步：
 * 1. add/update 新增或变化的元素
 * 2. remove 已被删除的元素
 */
function syncGraph(newNodes: NvlNode[], newRels: NvlRel[]): void {
  if (!nvl) return

  const styledNodes = styleNodes(newNodes)
  const styledRels = styleRels(newRels)

  // 新增 / 更新
  nvl.addAndUpdateElementsInGraph(styledNodes, styledRels)

  // 删除已不存在的节点
  const newNodeIds = new Set(newNodes.map((n) => n.id))
  const existingNodeIds = nvl.getNodes().map((n) => n.id)
  const removedNodeIds = existingNodeIds.filter((id) => !newNodeIds.has(id))
  if (removedNodeIds.length > 0) {
    nvl.removeNodesWithIds(removedNodeIds)
  }

  // 删除已不存在的关系
  const newRelIds = new Set(newRels.map((r) => r.id))
  const existingRelIds = nvl.getRelationships().map((r) => r.id)
  const removedRelIds = existingRelIds.filter((id) => !newRelIds.has(id))
  if (removedRelIds.length > 0) {
    nvl.removeRelationshipsWithIds(removedRelIds)
  }
}

// ─── 受控选中同步 ─────────────────────────────────────────────────────────────

function syncSelection(selectedIds: string[]): void {
  if (!nvl) return
  const selectedSet = new Set(selectedIds)
  const updates = nvl.getNodes().map((n) => ({
    id: n.id,
    selected: selectedSet.has(n.id),
  }))
  if (updates.length > 0) {
    nvl.updateElementsInGraph(updates, [])
  }
}

// ─── 公开方法（供父组件通过 ref 调用） ─────────────────────────────────────────

/** 缩放至所有节点可见 */
function fitAll(): void {
  nvl?.fit(
    props.nodes.map((n) => n.id),
    { animated: true }
  )
}

/** 重置缩放 */
function resetZoom(): void {
  nvl?.resetZoom()
}

/** 将画布另存为 PNG */
function saveAsPng(): void {
  nvl?.saveToFile()
}

/** 取消所有选中 */
function deselectAll(): void {
  nvl?.deselectAll()
}

/** 获取当前所有节点坐标（用于 Phase 4 保存布局位置） */
function getNodePositions() {
  return nvl?.getNodePositions() ?? []
}

/** 强制重新计算力导向布局（不保留旧坐标，节点打散重排） */
function forceRelayout(): void {
  if (!nvl) return
  nvl.restart(undefined, false)
}

defineExpose({ fitAll, resetZoom, saveAsPng, deselectAll, getNodePositions, forceRelayout })

// ─── 生命周期 & 侦听器 ────────────────────────────────────────────────────────

onMounted(() => {
  initNvl()

  // ResizeObserver：容器尺寸变化时重启渲染（保留节点位置）
  if (containerRef.value) {
    resizeObserver = new ResizeObserver(() => {
      nvl?.restart(undefined, true)
    })
    resizeObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  destroyNvl()
})

// 节点或关系数据变化 → 增量同步
watch(
  [() => props.nodes, () => props.rels],
  ([newNodes, newRels]) => {
    if (nvl) {
      syncGraph(newNodes, newRels)
    }
  },
  { deep: true }
)

// 受控选中 → 同步选中状态
watch(
  () => props.selectedNodeIds,
  (ids) => syncSelection(ids)
)

// mode 切换 → 重新注册 interactions（不重建图谱数据）
watch(
  () => props.mode,
  () => registerInteractions()
)

// layout 切换 → 调用 setLayout
watch(
  () => props.layout,
  (layout) => nvl?.setLayout(layout)
)
</script>

<template>
  <div class="nvl-graph-wrapper">
    <!-- 加载遮罩 -->
    <div v-if="loading" class="nvl-graph-loading">
      <a-spin size="large" />
    </div>

    <!-- 鼠标离开容器时清除 hover 状态 -->
    <div
      ref="containerRef"
      class="nvl-graph-container"
      @mouseleave="
        () => {
          hoveredNodeId = null
          emit('node-hover', null)
        }
      "
    />
  </div>
</template>

<style scoped>
@reference "#main.css";

.nvl-graph-wrapper {
  @apply relative w-full h-full;
}

.nvl-graph-container {
  @apply w-full h-full;
  min-height: 0;
}

.nvl-graph-loading {
  @apply absolute inset-0 z-10 flex items-center justify-center bg-white/60;
}
</style>
