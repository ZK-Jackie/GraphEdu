<script setup lang="ts">
/**
 * RouterTemplate - 通用路由面板组件
 *
 * 用于在 Golden Layout 中承载路由视图
 * 每个标签页独立渲染对应路由的组件（叶子组件，不包括布局组件）
 */
import type { BaseRouter } from '@/types/components/router.ts'
import { useRouter } from 'vue-router'

// 从 Golden Layout 的 componentState 接收路由信息
const props = defineProps<BaseRouter>()

const router = useRouter()

// 存储解析后的组件
const resolvedComponent = shallowRef<any>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)

// 将该 panel 的静态路由参数 provide 给内部组件
// 避免内部组件依赖全局 useRoute()，从而消除 KeepAlive 多实例重复触发问题
const panelRouteParams = computed(() => router.resolve(props.path || '').params)
provide('__panelRouteParams', panelRouteParams)

// 根据路由信息查找并加载对应的组件
const loadComponent = async () => {
  isLoading.value = true
  error.value = null

  try {
    // 通过路由路径解析匹配的路由记录数组
    const matched = router.resolve(props.path || '').matched

    if (!matched || matched.length === 0) {
      error.value = `未找到路由: ${props.path}`
      console.warn(error.value)
      return
    }

    // 获取最后一个匹配项（叶子路由），跳过父级布局组件
    const leafRoute = matched[matched.length - 1]

    if (!leafRoute) {
      error.value = `未找到叶子路由组件: ${props.name || props.path}`
      console.warn(error.value)
      return
    }

    // 布局入口路由不应作为面板内容渲染，否则会无限嵌套
    // 使用 meta.isLayoutEntry 标记（静态路由用）
    if (leafRoute.meta?.isLayoutEntry) {
      error.value = `跳过布局入口路由: ${props.path}`
      console.warn(error.value)
      return
    }

    let component = leafRoute.components?.default

    if (!component) {
      error.value = `路由组件未定义: ${props.name || props.path}`
      console.warn(error.value)
      return
    }

    // 如果是懒加载组件（函数），需要先加载
    if (typeof component === 'function' && !component.length) {
      // 检查是否是异步组件（动态导入）
      const result = (component as () => Promise<any>)()
      if (result instanceof Promise) {
        const module = await result
        component = module.default || module
      }
    }

    // 防止渲染布局组件本身（避免无限嵌套）
    const componentName = (component as any)?.name || (component as any)?.__name
    const LAYOUT_COMPONENT_NAMES = ['Layout', 'WorkbenchContent', 'StudentCourseLayout', 'TeacherCourseLayout']
    if (LAYOUT_COMPONENT_NAMES.includes(componentName)) {
      error.value = `跳过布局组件: ${componentName}`
      console.warn(error.value)
      return
    }

    resolvedComponent.value = component ? markRaw(component as object) : null
  } catch (e) {
    error.value = `加载组件失败: ${e}`
    console.error(error.value, e)
  } finally {
    isLoading.value = false
  }
}

// 组件挂载时加载
onMounted(() => {
  loadComponent()
})

// 监听路径变化（如果需要）
watch(
  () => props.path,
  () => {
    loadComponent()
  }
)
</script>

<template>
  <div class="router-panel">
    <!-- 加载中状态 -->
    <div v-if="isLoading" class="loading-message">加载中...</div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-message">{{ error }}</div>

    <!-- 正常渲染组件 -->
    <KeepAlive v-else-if="resolvedComponent">
      <component :is="resolvedComponent" />
    </KeepAlive>

    <!-- 无组件状态 -->
    <div v-else class="error-message">无法加载路由组件: {{ props.name || props.path }}</div>
  </div>
</template>

<style scoped>
.router-panel {
  width: 100%;
  height: 100%;
  padding-bottom: 20px;
}

.loading-message {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  font-size: 14px;
}

.error-message {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #ef4444;
  font-size: 14px;
}
</style>
