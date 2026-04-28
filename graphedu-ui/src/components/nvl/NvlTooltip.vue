<script setup lang="ts">
/**
 * NvlTooltip - 知识图谱节点悬浮提示
 *
 * 用法：
 *   <NvlTooltip :info="tooltipInfo" />
 *
 * 其中 tooltipInfo 来自 NvlGraph 的 @node-hover 事件：
 *   - 传入 TooltipInfo 对象时显示
 *   - 传入 null 时隐藏
 */
import type { TooltipInfo } from './types'
import { useNvlStyles } from './useNvlStyles'

interface Props {
  /** 悬浮信息；null 表示隐藏 */
  info: TooltipInfo | null
  /** 鼠标指针与 Tooltip 的偏移量（px），默认 [14, 8] */
  offset?: [number, number]
}

const props = withDefaults(defineProps<Props>(), {
  offset: () => [14, 8],
})

const { NODE_TYPE_COLORS, STATUS_COLORS } = useNvlStyles()

// ─── 延迟显示避免快速划过抖动 ─────────────────────────────────────────────────

const visible = ref(false)
let showTimer: ReturnType<typeof setTimeout> | null = null

watch(
  () => props.info,
  (val) => {
    if (showTimer) {
      clearTimeout(showTimer)
      showTimer = null
    }
    if (val) {
      showTimer = setTimeout(() => {
        visible.value = true
      }, 80)
    } else {
      visible.value = false
    }
  }
)

// ─── Tooltip 定位 ─────────────────────────────────────────────────────────────

const tooltipStyle = computed(() => {
  if (!props.info) return {}
  const [ox, oy] = props.offset
  return {
    left: `${props.info.x + ox}px`,
    top: `${props.info.y + oy}px`,
  }
})

// ─── 节点类型显示名称 ──────────────────────────────────────────────────────────

const NODE_TYPE_LABELS: Record<string, string> = {
  chapter: '章节',
  knowledge: '知识点',
  concept: '概念',
}

const STATUS_LABELS: Record<string, string> = {
  normal: '正常',
  unlearned: '未学习',
  learning: '学习中',
  mastered: '已掌握',
}

const nodeTypeLabel = computed(() => {
  const type = props.info?.node.nodeType
  return type ? NODE_TYPE_LABELS[type] : null
})

const statusLabel = computed(() => {
  const status = props.info?.node.status
  return status ? STATUS_LABELS[status] : null
})

/** 节点颜色（与图谱保持一致） */
const dotColor = computed(() => {
  const node = props.info?.node
  if (!node) return '#4C8EDA'
  if (node.color) return node.color
  if (node.status && node.status !== 'normal') return STATUS_COLORS[node.status]
  return NODE_TYPE_COLORS[node.nodeType ?? 'default'] ?? '#4C8EDA'
})

onUnmounted(() => {
  if (showTimer) clearTimeout(showTimer)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="nvl-tooltip-fade">
      <div v-if="visible && info" class="nvl-tooltip" :style="tooltipStyle" role="tooltip" aria-live="polite">
        <!-- 标题行 -->
        <div class="nvl-tooltip-title">
          <span class="nvl-tooltip-dot" :style="{ backgroundColor: dotColor }" />
          <span class="nvl-tooltip-name">
            {{ info.node.caption ?? info.node.id }}
          </span>
          <a-tag v-if="nodeTypeLabel" size="small" class="nvl-tooltip-tag">
            {{ nodeTypeLabel }}
          </a-tag>
        </div>

        <!-- 描述 -->
        <p v-if="info.node.description" class="nvl-tooltip-desc">
          {{ info.node.description }}
        </p>

        <!-- 学习状态（Phase 5） -->
        <div v-if="statusLabel" class="nvl-tooltip-meta">
          <span class="nvl-tooltip-meta-label">状态：</span>
          <span>{{ statusLabel }}</span>
        </div>

        <!-- 点击提示 -->
        <div class="nvl-tooltip-hint">
          <span v-if="info.node.routePath">点击跳转至学习页</span>
          <span v-else>点击查看详情</span>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.nvl-tooltip {
  position: fixed;
  z-index: 9999;
  pointer-events: none;
  background: rgba(255, 255, 255, 0.97);
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  padding: 10px 14px;
  min-width: 160px;
  max-width: 300px;
  font-size: 13px;
  line-height: 1.6;
  color: #333;
}

.nvl-tooltip-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.nvl-tooltip-dot {
  flex-shrink: 0;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.nvl-tooltip-name {
  font-weight: 600;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nvl-tooltip-tag {
  flex-shrink: 0;
  font-size: 11px;
}

.nvl-tooltip-desc {
  color: #666;
  margin: 4px 0;
  font-size: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.nvl-tooltip-meta {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.nvl-tooltip-meta-label {
  color: #999;
}

.nvl-tooltip-hint {
  margin-top: 6px;
  font-size: 11px;
  color: #aaa;
  border-top: 1px solid #f0f0f0;
  padding-top: 5px;
}

/* 进出场动画 */
.nvl-tooltip-fade-enter-active,
.nvl-tooltip-fade-leave-active {
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
}

.nvl-tooltip-fade-enter-from,
.nvl-tooltip-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
