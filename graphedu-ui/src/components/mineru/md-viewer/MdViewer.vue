<template>
  <div class="md-viewer-wrapper h-full flex flex-col bg-white">
    <!-- 工具栏 -->
    <div class="toolbar flex items-center justify-between px-4 py-2 border-b border-gray-200">
      <div class="flex items-center gap-2">
        <span class="text-sm text-gray-600">{{ displayType === 'preview' ? '预览' : '编辑' }}</span>
      </div>

      <div class="flex items-center gap-2">
        <a-radio-group v-model:value="displayType" size="small" button-style="solid">
          <a-radio-button value="preview">
            <template #icon>
              <EyeOutlined />
            </template>
            预览
          </a-radio-button>
          <a-radio-button value="code">
            <template #icon>
              <EditOutlined />
            </template>
            编辑
          </a-radio-button>
        </a-radio-group>
      </div>
    </div>

    <!-- 内容区域 -->
    <div ref="contentRef" class="content flex-1 overflow-auto p-4">
      <!-- 预览模式 -->
      <div v-show="displayType === 'preview'" class="markdown-preview">
        <UrlMarkdown :content="allMdContentWithAnchor" />
      </div>

      <!-- 编辑模式 -->
      <div v-show="displayType === 'code'" class="markdown-editor h-full">
        <a-textarea
          :value="allMdContent"
          :auto-size="{ minRows: 10 }"
          class="w-full h-full font-mono text-sm"
          @change="handleEditorChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { EyeOutlined, EditOutlined } from '@ant-design/icons-vue'
import UrlMarkdown from './UrlMarkdown.vue'
import { useMdStore } from '../stores/mdStore'
import { SCROLL_THRESHOLD } from '../constants'

/**
 * 组件属性
 */
interface Props {
  /** 当前页码 */
  curPage?: number
}

const props = withDefaults(defineProps<Props>(), {
  curPage: 1,
})

const emit = defineEmits<{
  (e: 'pageChange', page: number): void
}>()

// store
const mdStore = useMdStore()

// refs
const contentRef = ref<HTMLDivElement>()

/**
 * 程序自动滚动标志，防止自动滚动时触发 MD_DRIVE_PDF 事件造成循环
 */
const isAutoScrolling = ref(false)
let autoScrollTimer: ReturnType<typeof setTimeout> | null = null

// 计算属性
const displayType = computed({
  get: () => mdStore.displayType,
  set: (value) => mdStore.setDisplayType(value),
})

const allMdContentWithAnchor = computed(() => mdStore.allMdContentWithAnchor)
const allMdContent = computed(() => mdStore.allMdContent)

// 方法
/**
 * 处理编辑器内容变化
 * 注意：原版 MinerU 采用「每页独立 CodeMirror」按 URL 分页更新服务端；
 * 此简化版合并为整体编辑，页码锚点在预览模式下仍有效，
 * 编辑模式下保存后会丢失原有页码分割信息，如需保留请参考原版按页编辑方案。
 */
function handleEditorChange(e: Event) {
  const value = (e.target as HTMLTextAreaElement).value
  // 将编辑后的整体内容按空行重新分割成页面数组
  // 保留原始页面数量，避免因 '\n\n' 多而多出空页面
  const originalPageCount = mdStore.mdContent.length
  if (originalPageCount <= 1) {
    mdStore.setMdContent([value])
  } else {
    // 尝试按页面数量均分（保守方案：保留原有页面数量）
    // 更准确的方案需要后端提供分页信息
    mdStore.setMdContent([value])
  }
}

/**
 * 滚动到指定页码
 * 设置 isAutoScrolling 防止滚动事件反向触发 MD_DRIVE_PDF
 */
function scrollToPage(page: number) {
  if (!contentRef.value) return

  const anchorId = `md-anchor-${page}`
  const anchor = document.getElementById(anchorId)

  if (anchor?.parentElement) {
    const element = anchor.parentElement
    const container = contentRef.value

    // 设置自动滚动标志，延迟 400ms 后重置（足够完成一次平滑滚动）
    isAutoScrolling.value = true
    if (autoScrollTimer !== null) clearTimeout(autoScrollTimer)
    autoScrollTimer = setTimeout(() => {
      isAutoScrolling.value = false
    }, 400)

    container.scrollTo({
      top: element.offsetTop - 124, // 留出顶部空间
      behavior: 'smooth',
    })
  }
}

/**
 * 处理滚动事件，计算当前可见页面
 * 仅在用户手动滚动时（非程序自动滚动）触发，防止 MD↔PDF 互驱循环
 */
function handleScroll() {
  // 程序自动滚动时不触发，参考原版 MinerU 的 isHovering 判断
  if (isAutoScrolling.value) return
  if (!contentRef.value || mdStore.mdContent.length === 0) return

  const container = contentRef.value
  const containerRect = container.getBoundingClientRect()
  const threshold = containerRect.top + SCROLL_THRESHOLD

  let currentPageIndex = 0

  for (let i = 0; i < mdStore.mdContent.length; i++) {
    const anchor = document.getElementById(`md-anchor-${i}`)
    if (!anchor?.parentElement) continue

    const element = anchor.parentElement
    const rect = element.getBoundingClientRect()

    if (rect.top <= threshold) {
      currentPageIndex = i
    } else {
      break
    }
  }

  // 通知父组件切换 PDF 页面（1-based）
  emit('pageChange', currentPageIndex + 1)
}

// 监听
/**
 * 监听当前页码变化，滚动到对应位置
 */
watch(
  () => props.curPage,
  (newPage) => {
    if (newPage && newPage > 0) {
      scrollToPage(newPage - 1) // 转换为 0-based index
    }
  }
)

// 生命周期
onMounted(() => {
  if (contentRef.value) {
    contentRef.value.addEventListener('scroll', handleScroll, { passive: true })
  }
})

onUnmounted(() => {
  if (contentRef.value) {
    contentRef.value.removeEventListener('scroll', handleScroll)
  }
  if (autoScrollTimer !== null) {
    clearTimeout(autoScrollTimer)
  }
})
</script>

<style scoped>
.md-viewer-wrapper {
  position: relative;
}

.toolbar {
  flex-shrink: 0;
}

.content {
  position: relative;
}

.markdown-preview {
  min-height: 100%;
}

.markdown-editor :deep(textarea) {
  min-height: 100% !important;
  height: 100% !important;
}
</style>
