<script setup lang="ts">
import VueGoldenLayout from '@/components/VueGoldenLayout/index.vue'
import type { LayoutConfig } from 'golden-layout'
import type { BaseRouter } from '@/types/components/router.ts'
import { buildInitConfig } from './config.ts'
import { useRouter } from 'vue-router'

interface CourseContentProps {
  courseId: string | number
}

const props = defineProps<CourseContentProps>()

/**
 * 获取课程 ID（响应式，用于区分不同课程的布局缓存）
 */
const courseId = computed(() => props.courseId as string)

/**
 * 布局缓存 key 前缀，教师端使用独立 key 与学生端隔离
 */
const layoutKeyPrefix = inject<string>('layoutKeyPrefix', 'GRAPHEDU_TEACHER_COURSE_VGL_LAYOUT')

/**
 * 按课程 + 角色独立存储布局
 */
const localLayoutKey = computed(() => `${layoutKeyPrefix}_${courseId.value}`)

const route = useRoute()
const router = useRouter()
const layoutRef = ref<typeof VueGoldenLayout | null>(null)

const openedTabs = ref<Map<string, { refId: number; routeInfo: BaseRouter }>>(new Map())

let isUpdatingRoute = false
const isLayoutInitialized = ref(false)

const getRouteTitle = (routeInstance: typeof route) => {
  return (routeInstance.meta?.title as string) || routeInstance.name?.toString() || routeInstance.path
}

const openRouteInPanel = async (routePath: string, routeInstance = route) => {
  if (!layoutRef.value) return

  if (openedTabs.value.has(routePath)) {
    const tabInfo = openedTabs.value.get(routePath)
    if (tabInfo) {
      layoutRef.value.activateTabByRefId(tabInfo.refId)
      return
    }
  }

  const title = getRouteTitle(routeInstance)
  try {
    const openedRouteInfo: BaseRouter = {
      path: routeInstance.path,
      name: routeInstance.name?.toString() || '',
      params: routeInstance.params,
      query: routeInstance.query,
      meta: routeInstance?.meta,
    }

    await layoutRef.value.addComponent('RouterTemplate', title, openedRouteInfo)

    const config = layoutRef.value.getLayoutConfig()
    const newRefId = findLatestRefId(config)
    openedTabs.value.set(routePath, { refId: newRefId, routeInfo: openedRouteInfo })

    console.log(`[TeacherContent] 已打开: ${routePath}, refId: ${newRefId}`)
  } catch (error) {
    console.error(`[TeacherContent] 打开路由失败: ${routePath}`, error)
  }
}

const openRoute = async (path: string, _title: string) => {
  // 设置标志，避免 watch(route.path) 与直接调用 openRouteInPanel 重复执行
  isUpdatingRoute = true
  await router.push(path).catch(() => {
    // push 失败时重置标志，确保后续路由监听恢复正常
    isUpdatingRoute = false
  })
  await openRouteInPanel(path, route)
}

const findLatestRefId = (config: any): number => {
  let maxRefId = 0
  const traverse = (item: any) => {
    if (item.componentState?.refId !== undefined) {
      maxRefId = Math.max(maxRefId, item.componentState.refId)
    }
    if (item.content) item.content.forEach(traverse)
  }
  if (config.root) traverse(config.root)
  return maxRefId
}

const syncCurrentRouteToLayout = async () => {
  const currentPath = route.path
  if (currentPath === '/') return
  if (openedTabs.value.has(currentPath)) {
    const tabInfo = openedTabs.value.get(currentPath)
    if (tabInfo && layoutRef.value) layoutRef.value.activateTabByRefId(tabInfo.refId)
  } else {
    await openRouteInPanel(currentPath, route)
  }
}

const restoreOpenedTabsFromConfig = (config: LayoutConfig) => {
  const newOpenedTabs = new Map<string, { refId: number; routeInfo: BaseRouter }>()
  const traverse = (item: any) => {
    if (item.componentState?.path && item.componentState?.refId !== undefined) {
      const routePath = item.componentState.path as string
      const routeInfo: BaseRouter = {
        path: item.componentState.path,
        name: item.componentState.name ?? '',
        params: item.componentState.params ?? {},
        query: item.componentState.query ?? {},
        meta: item.componentState.meta ?? {},
      }
      newOpenedTabs.set(routePath, { refId: item.componentState.refId, routeInfo })
    }
    if (item.content) item.content.forEach(traverse)
  }
  if (config.root) traverse(config.root)
  openedTabs.value = newOpenedTabs
}

const handlePanelChange = (componentInfo: { vglComponentState?: any }) => {
  if (!componentInfo.vglComponentState) return
  const routeInfo = componentInfo.vglComponentState as BaseRouter
  const targetPath = routeInfo.path
  if (targetPath === route.path) return
  isUpdatingRoute = true
  router
    .push({ path: routeInfo.path, query: routeInfo.query ?? {}, params: routeInfo.params ?? {} })
    .catch((err: unknown) => {
      isUpdatingRoute = false
      if ((err as Error).name !== 'NavigationDuplicated') {
        console.warn('[TeacherContent] 路由跳转失败:', err)
      }
    })
  window.dispatchEvent(new Event('resize'))
}

const handleTabClose = (refId: number, componentState: any) => {
  if (!componentState) return
  const routePath = (componentState as BaseRouter).path
  if (routePath !== undefined && openedTabs.value.has(routePath)) {
    openedTabs.value.delete(routePath)
    console.log(`[TeacherContent] 标签页关闭: ${routePath}, refId: ${refId}`)
  }
}

watch(
  () => route.path,
  async (newPath: string, oldPath: string) => {
    if (!isLayoutInitialized.value) return
    if (isUpdatingRoute) {
      isUpdatingRoute = false
      return
    }
    if (newPath === '/' || newPath === oldPath) return
    await openRouteInPanel(newPath, route)
  },
  { immediate: false }
)

onMounted(async () => {
  if (layoutRef.value) {
    const saved = localStorage.getItem(localLayoutKey.value)
    if (saved) {
      try {
        const config = JSON.parse(saved) as LayoutConfig
        await layoutRef.value.loadLayout(config)
        restoreOpenedTabsFromConfig(config)
        isLayoutInitialized.value = true
      } catch {
        const initConfig = buildInitConfig(courseId.value)
        await layoutRef.value.loadLayout(initConfig)
        restoreOpenedTabsFromConfig(initConfig)
        isLayoutInitialized.value = true
      }
    } else {
      const initConfig = buildInitConfig(courseId.value)
      await layoutRef.value.loadLayout(initConfig)
      restoreOpenedTabsFromConfig(initConfig)
      isLayoutInitialized.value = true
    }

    layoutRef.value.registerOnFocusCallback(handlePanelChange)
    layoutRef.value.registerOnTabCloseCallback(handleTabClose)

    console.log('[TeacherContent] Golden Layout 初始化完成')
    await nextTick()
    await syncCurrentRouteToLayout()
  }
})

const saveLayout = () => {
  if (layoutRef.value) {
    localStorage.setItem(localLayoutKey.value, JSON.stringify(layoutRef.value.getLayoutConfig()))
  }
}

const loadSavedLayout = async () => {
  const saved = localStorage.getItem(localLayoutKey.value)
  if (saved && layoutRef.value) {
    try {
      await layoutRef.value.loadLayout(JSON.parse(saved) as LayoutConfig)
    } catch (error) {
      console.error('[TeacherContent] 加载保存布局失败:', error)
    }
  }
}

defineExpose({ saveLayout, loadSavedLayout, layoutRef, openRouteInPanel, openRoute, openedTabs })
</script>

<template>
  <VueGoldenLayout ref="layoutRef" class="course-golden-layout" />
</template>

<style scoped>
.course-golden-layout {
  width: 100%;
  height: 100%;
}
</style>
