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
 * 布局缓存 key 前缀，学生端/教师端分别注入不同前缀以隔离 localStorage
 * 默认：GRAPHEDU_COURSE_VGL_LAYOUT（学生端）
 */
const layoutKeyPrefix = inject<string>('layoutKeyPrefix', 'GRAPHEDU_COURSE_VGL_LAYOUT')

/**
 * 按课程 + 角色独立存储布局
 */
const localLayoutKey = computed(() => `${layoutKeyPrefix}_${courseId.value}`)

// 当前路由
const route = useRoute()
// 路由器实例
const router = useRouter()
// Golden Layout 组件引用
const layoutRef = ref<typeof VueGoldenLayout | null>(null)

/**
 * 已打开的路由标签页记录
 * 键：路由路径，值：{ refId, routeInfo }
 */
const openedTabs = ref<Map<string, { refId: number; routeInfo: BaseRouter }>>(new Map())

/**
 * 防止路由循环更新的标志
 */
let isUpdatingRoute = false

/**
 * 标记 Golden Layout 是否已初始化
 */
const isLayoutInitialized = ref(false)

/**
 * 根据路由信息生成标签页标题
 */
const getRouteTitle = (routeInstance: typeof route) => {
  return (routeInstance.meta?.title as string) || routeInstance.name?.toString() || routeInstance.path
}

/**
 * 在 Golden Layout 中打开路由页面
 * @param routePath 打开的路由路径
 * @param routeInstance 路由实例（可选，默认使用当前路由）
 */
const openRouteInPanel = async (routePath: string, routeInstance = route) => {
  if (!layoutRef.value) return

  // 检查是否已经打开该路由
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

    console.log(`[CourseContent] 已打开: ${routePath}, refId: ${newRefId}`)
  } catch (error) {
    console.error(`[CourseContent] 打开路由失败: ${routePath}`, error)
  }
}

/**
 * 打开指定路由（供外部组件调用，先推进路由再同步到 GL）
 */
const openRoute = async (path: string, title: string) => {
  // 设置标志，避免 watch(route.path) 与直接调用 openRouteInPanel 重复执行
  isUpdatingRoute = true
  await router.push(path).catch(() => {
    // push 失败时重置标志，确保后续路由监听恢复正常
    isUpdatingRoute = false
  })
  await openRouteInPanel(path, route)
}

/**
 * 从布局配置中查找最新的 refId（最大值）
 */
const findLatestRefId = (config: any): number => {
  let maxRefId = 0
  const traverse = (item: any) => {
    if (item.componentState?.refId !== undefined) {
      maxRefId = Math.max(maxRefId, item.componentState.refId)
    }
    if (item.content) {
      item.content.forEach(traverse)
    }
  }
  if (config.root) traverse(config.root)
  return maxRefId
}

/**
 * 同步当前路由到 Golden Layout
 */
const syncCurrentRouteToLayout = async () => {
  const currentPath = route.path
  if (currentPath === '/') return

  if (openedTabs.value.has(currentPath)) {
    const tabInfo = openedTabs.value.get(currentPath)
    if (tabInfo && layoutRef.value) {
      layoutRef.value.activateTabByRefId(tabInfo.refId)
    }
  } else {
    await openRouteInPanel(currentPath, route)
  }
}

/**
 * 从布局配置中重建 openedTabs 映射
 */
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
      newOpenedTabs.set(routePath, {
        refId: item.componentState.refId,
        routeInfo,
      })
    }
    if (item.content) {
      item.content.forEach(traverse)
    }
  }

  if (config.root) traverse(config.root)
  openedTabs.value = newOpenedTabs
  console.log(`[CourseContent] 已恢复 ${newOpenedTabs.size} 个标签页`, Array.from(newOpenedTabs.keys()))
}

/**
 * 处理标签页激活事件 → 同步 Vue Router
 */
const handlePanelChange = (componentInfo: { vglComponentState?: any }) => {
  if (!componentInfo.vglComponentState) return

  const routeInfo = componentInfo.vglComponentState as BaseRouter
  const targetPath = routeInfo.path

  if (targetPath === route.path) return

  isUpdatingRoute = true

  router
    .push({
      path: routeInfo.path,
      query: routeInfo.query ?? {},
      params: routeInfo.params ?? {},
    })
    .catch((err: unknown) => {
      isUpdatingRoute = false
      if ((err as Error).name !== 'NavigationDuplicated') {
        console.warn('[CourseContent] 路由跳转失败:', err)
      }
    })

  window.dispatchEvent(new Event('resize'))
  console.log('[CourseContent] 标签页激活，路由更新:', targetPath)
}

/**
 * 处理标签页关闭事件
 */
const handleTabClose = (refId: number, componentState: any) => {
  if (!componentState) return

  const routeInfo = componentState as BaseRouter
  const routePath = routeInfo.path

  if (routePath !== undefined && openedTabs.value.has(routePath)) {
    openedTabs.value.delete(routePath)
    console.log(`[CourseContent] 标签页关闭: ${routePath}, refId: ${refId}`)
  }
}

/**
 * 监听路由变化，自动打开新标签页
 */
watch(
  () => route.path,
  async (newPath: string, oldPath: string) => {
    if (!isLayoutInitialized.value) return
    if (isUpdatingRoute) {
      isUpdatingRoute = false
      return
    }
    if (newPath === '/' || newPath === oldPath) return

    console.log(`[CourseContent] 路由变化: ${oldPath} → ${newPath}`)
    await openRouteInPanel(newPath, route)
  },
  { immediate: false }
)

/**
 * 组件挂载后加载布局
 */
onMounted(async () => {
  if (layoutRef.value) {
    const saved = localStorage.getItem(localLayoutKey.value)
    if (saved) {
      try {
        const config = JSON.parse(saved) as LayoutConfig
        await layoutRef.value.loadLayout(config)
        restoreOpenedTabsFromConfig(config)
        isLayoutInitialized.value = true
        console.log('[CourseContent] 已加载保存的布局')
      } catch (error) {
        console.warn('[CourseContent] 加载保存布局失败，使用默认布局', error)
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

    console.log('[CourseContent] Golden Layout 初始化完成')

    await nextTick()
    await syncCurrentRouteToLayout()
  }
})

/**
 * 保存当前布局配置
 */
const saveLayout = () => {
  if (layoutRef.value) {
    const config = layoutRef.value.getLayoutConfig()
    localStorage.setItem(localLayoutKey.value, JSON.stringify(config))
  }
}

/**
 * 加载保存的布局
 */
const loadSavedLayout = async () => {
  const saved = localStorage.getItem(localLayoutKey.value)
  if (saved && layoutRef.value) {
    try {
      const config = JSON.parse(saved) as LayoutConfig
      await layoutRef.value.loadLayout(config)
    } catch (error) {
      console.error('[CourseContent] 加载保存布局失败:', error)
    }
  }
}

defineExpose({
  saveLayout,
  loadSavedLayout,
  layoutRef,
  openRouteInPanel,
  openRoute,
  openedTabs,
})
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
