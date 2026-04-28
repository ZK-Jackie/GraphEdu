<template>
  <div ref="pageRef" class="pdf-page relative" :data-page-number="pageNum" :style="pageStyle">
    <!-- 占位：不在可见范围时仅渲染空白占位保持滚动条高度 -->
    <template v-if="!shouldRender">
      <div class="page-placeholder" :style="placeholderStyle" />
    </template>

    <!-- 实际渲染 -->
    <template v-else>
      <div class="page-content" :style="contentStyle">
        <!-- PDF 内容 -->
        <div class="canvas-wrapper">
          <canvas ref="canvasRef" />
        </div>

        <!-- 标注层（bbox 矩形框） -->
        <canvas ref="annotationCanvasRef" class="annotation-canvas" />

        <!-- 文本层（可选中） -->
        <div ref="textLayerRef" class="textLayer" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount, nextTick, inject } from 'vue'
import { usePdfPageRenderer } from './usePdfPageRenderer'
import { usePdfTextLayer } from './usePdfTextLayer'
import { usePdfAnnotationLayer } from './usePdfAnnotationLayer'
import type { BboxItem } from './usePdfAnnotationLayer'
import type { PageSize } from './types'

/**
 * 组件属性
 */
interface Props {
  /** 页码（1-based） */
  pageNum: number
  /** 是否应渲染（由虚拟滚动控制） */
  shouldRender: boolean
  /** 缩放比例 */
  scale: number
  /** PDF 页面代理（shouldRender=true 时传入） */
  pdfPage: any
  /** 页面原始尺寸（PDF points，scale=1 时的像素） */
  pageSize: PageSize
  /** 旋转角度 */
  rotation?: number
  /** 当前页的标注框列表 */
  bboxes?: BboxItem[]
}

const props = withDefaults(defineProps<Props>(), {
  rotation: 0,
})

// 从父组件注入页面高度更新回调（可选）
const onPageSizeMeasured = inject<((pageNum: number, size: PageSize) => void) | null>('onPageSizeMeasured', null)

const pageRef = ref<HTMLElement>()
const canvasRef = ref<HTMLCanvasElement>()
const annotationCanvasRef = ref<HTMLCanvasElement>()
const textLayerRef = ref<HTMLElement>()

const pageRenderer = usePdfPageRenderer()
const textLayer = usePdfTextLayer()
const annotationLayer = usePdfAnnotationLayer()

// 计算页面样式
const pageStyle = computed(() => {
  const { width, height } = getScaledSize()
  return {
    width: `${width}px`,
    height: `${height}px`,
  }
})

const placeholderStyle = computed(() => ({
  width: '100%',
  height: '100%',
  background: 'var(--ge-bg-elevated, #fafafa)',
}))

const contentStyle = computed(() => {
  const { width, height } = getScaledSize()
  return {
    width: `${width}px`,
    height: `${height}px`,
  }
})

function getScaledSize(): { width: number; height: number } {
  return {
    width: props.pageSize.width * props.scale,
    height: props.pageSize.height * props.scale,
  }
}

// 渲染逻辑
async function doRender(): Promise<void> {
  if (!props.pdfPage || !canvasRef.value) return

  const viewport = props.pdfPage.getViewport({
    scale: props.scale,
    rotation: props.rotation,
  })

  // 通知父组件实际测量到的页面尺寸
  onPageSizeMeasured?.(props.pageNum, {
    width: viewport.width / props.scale,
    height: viewport.height / props.scale,
  })

  // 渲染 canvas
  await pageRenderer.renderPage(props.pdfPage, canvasRef.value, props.scale, props.rotation)

  // 渲染文本层
  if (textLayerRef.value) {
    await textLayer.renderTextLayer(props.pdfPage, textLayerRef.value, viewport)
  }

  // 渲染标注层
  if (annotationCanvasRef.value && props.bboxes && props.bboxes.length > 0) {
    annotationLayer.renderAnnotations(annotationCanvasRef.value, props.bboxes, props.scale)
  }
}

function doCleanup(): void {
  pageRenderer.cancelRender()
  if (textLayerRef.value) {
    textLayer.clearTextLayer(textLayerRef.value)
  }
  if (annotationCanvasRef.value) {
    annotationLayer.clearAnnotations(annotationCanvasRef.value)
  }
  if (canvasRef.value) {
    const ctx = canvasRef.value.getContext('2d')
    if (ctx) {
      ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
    }
    canvasRef.value.width = 0
    canvasRef.value.height = 0
  }
}

// 监听 shouldRender 和 scale 变化
watch(
  () => [props.shouldRender, props.scale, props.pdfPage] as const,
  async ([shouldRender]) => {
    if (!shouldRender) {
      doCleanup()
      return
    }
    await nextTick()
    await doRender()
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  doCleanup()
})
</script>

<style scoped>
.pdf-page {
  margin: 0 auto 12px;
  flex-shrink: 0;
}

.page-content {
  position: relative;
  box-shadow: var(--ge-shadow, 0 2px 8px rgba(0, 0, 0, 0.15));
  background: white;
}

.canvas-wrapper {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.canvas-wrapper canvas {
  display: block;
}

.annotation-canvas {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: -1;
}

/*
 * 文本层样式 — 完整移植自 pdfjs 官方 text_layer_builder.css
 * pdfjs TextLayer.render() 依赖 CSS 变量（--font-height, --scale-x 等）
 * 以下规则将这些变量转换为实际的 font-size / transform，缺一不可
 */
.textLayer {
  color-scheme: only light;
  position: absolute;
  text-align: initial;
  inset: 0;
  overflow: clip;
  opacity: 1;
  line-height: 1;
  text-size-adjust: none;
  forced-color-adjust: none;
  transform-origin: 0 0;
  caret-color: CanvasText;
  z-index: 0;

  /* pdfjs 用 --min-font-size 绕过浏览器最小字体限制 */
  --min-font-size: 1;
  --text-scale-factor: calc(var(--total-scale-factor) * var(--min-font-size));
  --min-font-size-inv: calc(1 / var(--min-font-size));
}

.textLayer :deep(:is(span, br)) {
  color: transparent;
  position: absolute;
  white-space: pre;
  cursor: text;
  transform-origin: 0% 0%;
}

/* 关键规则：将 pdfjs 设置的 CSS 变量转为实际字号和变换 */
.textLayer :deep(> :not(.markedContent)),
.textLayer :deep(.markedContent span:not(.markedContent)) {
  z-index: 1;
  --font-height: 0;
  font-size: calc(var(--text-scale-factor) * var(--font-height));
  --scale-x: 1;
  --rotate: 0deg;
  transform: rotate(var(--rotate)) scaleX(var(--scale-x)) scale(var(--min-font-size-inv));
}

.textLayer :deep(.markedContent) {
  display: contents;
}

.textLayer :deep(span[role='img']) {
  user-select: none;
  cursor: default;
}

.textLayer :deep(.endOfContent) {
  display: block;
  position: absolute;
  inset: 100% 0 0;
  z-index: 0;
  cursor: default;
  user-select: none;
}

.textLayer :deep(.selecting .endOfContent) {
  top: 0;
}

.textLayer :deep(::selection) {
  background: rgba(0, 0, 255, 0.25);
}

.textLayer :deep(br::selection) {
  background: transparent;
}
</style>
