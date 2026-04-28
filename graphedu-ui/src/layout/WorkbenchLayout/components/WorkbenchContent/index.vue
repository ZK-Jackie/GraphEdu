<script setup lang="ts">
import VueGoldenLayout from '@/components/VueGoldenLayout/index.vue'
import type { LayoutConfig } from 'golden-layout'
import type { BaseRouter } from '@/types/components/router.ts'
import { initConfig } from './config.ts'
import { LocalVglLayoutKey } from '@/constants.ts'
import { useRouter } from 'vue-router'

/**
 * 响应式数据
 */
// 当前路由
const route = useRoute()
// 路由器实例
const router = useRouter()
// 布局对象
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
  // 优先使用路由 meta 中定义的标题
  return (routeInstance.meta?.title as string) || routeInstance.name?.toString() || routeInstance.path
}

/**
 * 在 Golden Layout 中打开路由页面（当路由变化时触发）
 * @param routePath 打开的路由路径
 * @param routeInstance 路由实例（可选，默认使用当前路由）
 */
const openRouteInPanel = async (routePath: string, routeInstance = route) => {
  if (!layoutRef.value) return

  // 检查是否已经打开该路由
  if (openedTabs.value.has(routePath)) {
    const tabInfo = openedTabs.value.get(routePath)
    if (tabInfo) {
      console.log(`路由 ${routePath} 已打开，激活标签页`)
      // 激活已存在的标签页
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

    // 使用通用的 RouterPanel 组件
    // addComponent 返回新创建的 refId
    const newRefId = await layoutRef.value.addComponent('RouterTemplate', title, openedRouteInfo)

    // 记录已打开的标签页
    openedTabs.value.set(routePath, {
      refId: newRefId,
      routeInfo: openedRouteInfo,
    })

    console.log(`[WorkbenchContent] 打开路由: ${routePath}, refId: ${newRefId}`)
  } catch (error) {
    console.error(`[WorkbenchContent] 打开路由失败: ${routePath}`, error)
  }
}

/**
 * 同步当前路由到 Golden Layout
 * 用于初始化或刷新页面时，确保当前路由对应的标签页已打开
 * 如果用户直接访问某个路由（如 /system/user），需要手动打开对应的标签页
 */
const syncCurrentRouteToLayout = async () => {
  const currentPath = route.path

  // 跳过根路径（使用 CommonLayout 的营销首页）
  if (currentPath === '/') {
    return
  }

  // 检查当前路由是否已经打开
  if (openedTabs.value.has(currentPath)) {
    // 已打开，激活该标签页
    const tabInfo = openedTabs.value.get(currentPath)
    if (tabInfo && layoutRef.value) {
      console.log(`激活已存在的标签页: ${currentPath}`)
      layoutRef.value.activateTabByRefId(tabInfo.refId)
    }
  } else {
    // 未打开，打开新标签页
    console.log(`当前路由 ${currentPath} 未打开，正在打开标签页...`)
    await openRouteInPanel(currentPath, route)
  }
}

/**
 * 从布局配置中重建 openedTabs 映射
 * 用于从 localStorage 加载布局后，恢复已打开的标签页记录
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

  // 更新 openedTabs
  openedTabs.value = newOpenedTabs

  console.log(`已恢复 ${newOpenedTabs.size} 个标签页记录`, Array.from(newOpenedTabs.keys()))
}

/**
 * 处理标签页激活事件
 * 当用户点击不同的标签页时，同步更新 Vue Router
 */
const handlePanelChange = (componentInfo: { vglComponentState?: any }) => {
  if (!componentInfo?.vglComponentState) return

  const routeInfo = componentInfo.vglComponentState as BaseRouter
  const targetPath = routeInfo.path

  // 如果路由已经是最新的，不需要更新
  if (targetPath === route.path) return

  // 防止循环更新
  isUpdatingRoute = true

  // 更新路由（恢复完整参数）
  router
    .push({
      path: routeInfo.path,
      query: routeInfo.query ?? {},
      params: routeInfo.params ?? {},
    })
    .then(() => {
      // 导航成功后，由 watch 消费 isUpdatingRoute 标志
    })
    .catch((err) => {
      // 路由跳转失败时立即重置标志
      isUpdatingRoute = false
      // 重复导航错误是正常的，不需要打印
      if (err.name !== 'NavigationDuplicated') {
        console.warn('[WorkbenchContent] 路由跳转失败:', err)
      }
    })
  // 触发页面重算，主要服务于表格页面的渲染
  window.dispatchEvent(new Event('resize'))
  console.log('[WorkbenchContent] 标签页激活，路由已更新:', targetPath)
}

/**
 * 处理标签页关闭事件
 * 当用户关闭标签页时，从 openedTabs 中移除记录
 */
const handleTabClose = (refId: number, componentState: any) => {
  if (!componentState) return

  const routeInfo = componentState as BaseRouter
  const routePath = routeInfo.path

  // 从 openedTabs 中移除记录
  if (routePath !== undefined && openedTabs.value.has(routePath)) {
    openedTabs.value.delete(routePath)
    console.log(`[LayoutContent] 标签页已关闭，已从记录中移除: ${routePath}, refId: ${refId}`)
  }
}

/**
 * 监听路由变化，自动打开新标签页
 */
watch(
  () => route.path,
  async (newPath, oldPath) => {
    // 如果布局还未初始化完成，跳过
    if (!isLayoutInitialized.value) {
      return
    }

    // 如果是标签页激活触发的路由变化，跳过
    if (isUpdatingRoute) {
      isUpdatingRoute = false
      return
    }

    // 跳过根路径或相同路径
    if (newPath === '/' || newPath === oldPath) {
      return
    }

    console.log(`路由变化: ${oldPath} → ${newPath}`, route)
    await openRouteInPanel(newPath, route)
  },
  { immediate: false } // 不立即执行，等待 Golden Layout 初始化完成
)

/**
 * 组件挂载后加载默认布局
 */
onMounted(async () => {
  if (layoutRef.value) {
    // 检查是否有保存的布局
    const saved = localStorage.getItem(LocalVglLayoutKey)
    if (saved) {
      try {
        const config = JSON.parse(saved) as LayoutConfig
        await layoutRef.value.loadLayout(config)

        // 从保存的布局中恢复已打开的标签页记录
        restoreOpenedTabsFromConfig(config)

        // 标记布局已初始化
        isLayoutInitialized.value = true

        console.log('已加载保存的布局')
      } catch (error) {
        console.warn('加载保存的布局失败，使用默认布局', error)

        // 加载空白布局
        await layoutRef.value.loadLayout(initConfig)
        restoreOpenedTabsFromConfig(initConfig)
        // 标记布局已初始化
        isLayoutInitialized.value = true
      }
    } else {
      // 加载空白布局
      await layoutRef.value.loadLayout(initConfig)

      // 恢复初始标签页记录（loadLayout 会将 refId 注入到 initConfig 中）
      restoreOpenedTabsFromConfig(initConfig)

      // 标记布局已初始化
      isLayoutInitialized.value = true
    }

    // 注册标签页焦点变化回调
    layoutRef.value.registerOnFocusCallback(handlePanelChange)

    // 注册标签页关闭回调
    layoutRef.value.registerOnTabCloseCallback(handleTabClose)

    console.log('Golden Layout 初始化完成')

    // 初始化完成后，检查当前路由是否需要在 Golden Layout 中打开
    // 如果用户直接访问某个路由（如 /system/user），需要手动打开对应的标签页
    await nextTick() // 等待 DOM 更新完成
    await syncCurrentRouteToLayout()
  }
})

/**
 * 保存当前布局配置（可选功能）
 */
const saveLayout = () => {
  if (layoutRef.value) {
    const config = layoutRef.value.getLayoutConfig()
    console.log('Current layout config:', config)
    localStorage.setItem(LocalVglLayoutKey, JSON.stringify(config))
  }
}

/**
 * 加载保存的布局（可选功能）
 */
const loadSavedLayout = async () => {
  const saved = localStorage.getItem(LocalVglLayoutKey)
  if (saved && layoutRef.value) {
    try {
      const config = JSON.parse(saved) as LayoutConfig
      await layoutRef.value.loadLayout(config)
    } catch (error) {
      console.error('Failed to load saved layout:', error)
    }
  }
}

// 暴露方法供外部调用（可选）
defineExpose({
  saveLayout,
  loadSavedLayout,
  layoutRef,
  openRouteInPanel, // 暴露打开路由的方法
  openedTabs, // 暴露已打开的标签页列表
})
</script>

<template>
  <VueGoldenLayout ref="layoutRef" class="golden-layout-container" />
</template>

<style scoped></style>
