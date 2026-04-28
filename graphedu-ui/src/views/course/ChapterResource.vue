<script setup lang="ts">
/**
 * ChapterResource.vue — 章节学习资源展示页
 *
 * 从路由参数中读取 chapterId，加载该章节下的所有资源，
 * 使用 VueGoldenLayout 以多 Tab 的方式展示：
 *   - document → ChapterPdfPanel（PDF.js iframe）
 *   - video    → ChapterVideoPanel（HTML5 video）
 *   - text     → ChapterTextPanel（Markdown 渲染）
 *
 * 所有 Tab 不支持关闭（isClosable: false）。
 */
import VueGoldenLayout from '@/components/VueGoldenLayout/index.vue'
import { getResourcesByChapter } from '@/api/education/chapterResource.ts'
import { getChapterDetail } from '@/api/education/chapter.ts'
import { getCourseDetail } from '@/api/education/course.ts'
import { reportLearningEvent } from '@/api/education/learning_event.ts'
import type { LayoutConfig, ComponentItemConfig } from 'golden-layout'
import type { FileInfoVO } from '@/types/api/system/upload.ts'
import type { CourseDetailVO } from '@/types/api/education/course.ts'
import type { ChapterDetailVO } from '@/types/api/chapter.ts'
import type { ChapterResourceListVO } from '@/types/api/education/chapterResource.ts'

// ─── 路由 ────────────────────────────────────────────────────────────────────

const route = useRoute()
// 从 RouterTemplate 注入该 tab 专属的路由参数，脱离全局 useRoute() 的响应式依赖
// 这样每个 KeepAlive 存活的实例只在自己 mount 时加载一次，不会随全局路由变化重复触发
const panelParams = inject<{ readonly value: Record<string, string | string[]> }>('__panelRouteParams')
let chapterId = 0
let courseId = 0

// 层级信息（用于构建引用来源）
const hierarchyInfo = ref<{
  courseName: string
  chapterName: string
}>({
  courseName: '',
  chapterName: '',
})

// ─── 状态 ────────────────────────────────────────────────────────────────────

const isLoading = ref(true)
const resources = ref<ChapterResourceListVO[]>([])
const layoutRef = ref<typeof VueGoldenLayout | null>(null)
const isLoadingHierarchy = ref(true)

// ─── 资源加载 ─────────────────────────────────────────────────────────────────

/**
 * MIME type → Golden Layout componentType 映射
 * 根据文件 MIME 类型决定使用哪个 Panel 渲染
 */
const FILE_TYPE_MAP: Record<string, string> = {
  // PDF → PdfPanel
  'application/pdf': 'ChapterPdfPanel',
  // Word → OfficePanel
  'application/msword': 'ChapterOfficePanel',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'ChapterOfficePanel',
  // Excel → OfficePanel
  'application/vnd.ms-excel': 'ChapterOfficePanel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'ChapterOfficePanel',
  // PPT → OfficePanel
  'application/vnd.ms-powerpoint': 'ChapterOfficePanel',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'ChapterOfficePanel',
  // Video → VideoPanel
  'video/mp4': 'ChapterVideoPanel',
  'video/x-msvideo': 'ChapterVideoPanel',
  'video/x-matroska': 'ChapterVideoPanel',
  'video/quicktime': 'ChapterVideoPanel',
  'video/x-ms-wmv': 'ChapterVideoPanel',
  // Text → TextPanel
  'text/plain': 'ChapterTextPanel',
  'text/markdown': 'ChapterTextPanel',
}

/**
 * resource_type 降级映射（当 MIME 无法匹配时使用）
 */
const RESOURCE_TYPE_FALLBACK: Record<string, string> = {
  video: 'ChapterVideoPanel',
  document: 'ChapterPdfPanel',
  text: 'ChapterTextPanel',
  binary: 'ChapterBinaryPanel',
  archive: 'ChapterBinaryPanel',
}

/**
 * 根据 MIME type 推断 officeType（供 ChapterOfficePanel 使用）
 */
function resolveOfficeType(fileType?: string): 'word' | 'excel' | 'pptx' | undefined {
  if (!fileType) return undefined
  if (fileType.includes('wordprocessingml') || fileType === 'application/msword') {
    return 'word'
  }
  if (fileType.includes('spreadsheetml') || fileType === 'application/vnd.ms-excel') {
    return 'excel'
  }
  if (fileType.includes('presentationml') || fileType === 'application/vnd.ms-powerpoint') {
    return 'pptx'
  }
  return undefined
}

/**
 * 根据文件信息决定使用哪个 Panel
 * 优先使用 MIME type 映射，降级使用 resource_type 映射
 */
function resolvePanelType(fileInfo?: FileInfoVO | null, resourceType?: string): string {
  if (fileInfo?.fileType) {
    const matched = FILE_TYPE_MAP[fileInfo.fileType]
    if (matched) return matched
  }
  return RESOURCE_TYPE_FALLBACK[resourceType ?? ''] ?? 'ChapterBinaryPanel'
}

/**
 * 将资源列表转换为 Golden Layout 配置
 * 使用 stack 类型（多标签页），每个资源对应一个不可关闭的 Tab
 */
const buildLayoutConfig = (list: ChapterResourceListVO[]): LayoutConfig => {
  const content: ComponentItemConfig[] = list.map((res) => {
    const componentType = resolvePanelType(res.fileInfo, res.resourceType)
    const officeType = resolveOfficeType(res.fileInfo?.fileType)

    return {
      type: 'component',
      title: res.resourceName,
      isClosable: false,
      header: { show: 'top' },
      componentType,
      componentState: {
        resourceId: res.resourceId,
        resourceName: res.resourceName,
        fileId: res.fileId,
        fileUrl: res.fileUrl,
        resourceUrl: res.resourceUrl,
        description: res.description,
        officeType,
        fileInfo: res.fileInfo ?? undefined,
        // 传递层级信息，用于构建引用来源
        courseName: hierarchyInfo.value.courseName,
        chapterName: hierarchyInfo.value.chapterName,
      },
    } as ComponentItemConfig
  })

  return {
    root: {
      type: 'stack',
      content,
    },
  }
}

/**
 * 加载层级信息（课程名、章节名）
 */
const loadHierarchyInfo = async () => {
  if (!chapterId || !courseId) return

  isLoadingHierarchy.value = true
  try {
    // 并行加载课程和章节信息
    const [courseRes, chapterRes] = await Promise.all([
      getCourseDetail(Number(courseId)),
      getChapterDetail(Number(chapterId)),
    ])

    if (courseRes.code === 200 && courseRes.data) {
      hierarchyInfo.value.courseName = courseRes.data.courseName || '课程'
    }

    if (chapterRes.code === 200 && chapterRes.data) {
      hierarchyInfo.value.chapterName = chapterRes.data.chapterName || '章节'
    }
  } catch (e) {
    console.error('[ChapterResource] 加载层级信息失败', e)
  } finally {
    isLoadingHierarchy.value = false
  }
}

/**
 * 加载章节资源并初始化布局
 */
const loadResources = async () => {
  if (!chapterId) return

  isLoading.value = true
  try {
    const res = await getResourcesByChapter(chapterId)
    if (res.code === 200 && res.data) {
      // 过滤：只展示正常状态且可见的资源，按显示顺序排序
      resources.value = res.data
        .filter((r) => r.status === '0' && r.isVisible === 'Y')
        .sort((a, b) => a.displayOrder - b.displayOrder)
    }
  } catch (e) {
    console.error('[ChapterResource] 加载资源失败', e)
  } finally {
    isLoading.value = false
  }
}

/**
 * 资源加载完毕后，将配置注入 VueGoldenLayout
 */
watch(
  [resources, layoutRef],
  async ([list, layout]) => {
    if (!layout || list.length === 0) return
    const config = buildLayoutConfig(list)
    await nextTick()
    await layout.loadLayout(config)
  },
  { immediate: false }
)

onMounted(() => {
  const rawChapterId = panelParams?.value?.['chapterId'] ?? route.params['chapterId']
  const rawCourseId = panelParams?.value?.['courseId'] ?? route.params['courseId']
  chapterId = Number(rawChapterId)
  courseId = Number(rawCourseId)

  // 同时加载层级信息和资源列表
  loadHierarchyInfo()
  loadResources()

  // 上报 chapter_open 事件（静默，不阻塞页面加载）
  if (courseId && chapterId) {
    reportLearningEvent({
      courseId,
      eventType: 'chapter_open',
      chapterId,
    }).catch(() => {
      // 事件上报失败不影响页面使用
    })
  }
})
</script>

<template>
  <div class="chapter-resource h-full w-full flex flex-col">
    <!-- 加载中 -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center">
      <a-spin size="large" tip="正在加载章节资源..." />
    </div>

    <!-- 无资源 -->
    <div v-else-if="resources.length === 0" class="flex-1 flex items-center justify-center">
      <a-empty description="该章节暂无学习资源" :image-style="{ height: '80px' }" />
    </div>

    <!-- 有资源：VueGoldenLayout 多 Tab 展示 -->
    <VueGoldenLayout v-else ref="layoutRef" class="chapter-resource-layout" />
  </div>
</template>

<style scoped>
.chapter-resource {
  overflow: hidden;
}

.chapter-resource-layout {
  width: 100%;
  height: 100%;
}
</style>
