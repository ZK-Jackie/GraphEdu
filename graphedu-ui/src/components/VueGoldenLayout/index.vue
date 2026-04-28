<script setup lang="ts">
import { ref } from 'vue'
import { LayoutConfig, VirtualLayout } from 'golden-layout'

import type {
  ComponentContainer,
  Json,
  RowOrColumnItemConfig,
  StackItemConfig,
  ComponentItem,
  ComponentItemConfig,
  ResolvedComponentItemConfig,
  LogicalZIndex,
  ResolvedLayoutConfig,
} from 'golden-layout'
import GlComponentWrapper from './GlComponentWrapper.vue'

/** Golden Layout 补充类型 **/
type AnyItemConfig = RowOrColumnItemConfig | StackItemConfig | VglComponentItemConfig

interface VglComponentItemConfig extends ComponentItemConfig {
  componentState: (Json & { refId: number }) | undefined
}

interface ResolvedVglComponentInfo {
  refId: number
  vglComponent: typeof GlComponentWrapper
  vglComponentState?: any
}

interface VglLayoutState {
  focus: ComponentItem | null
}

/**
 * Vue 组件 Props
 */

/**
 * 组件内部数据
 */
// vglLayout: Golden Layout 的核心实例，负责管理整个布局系统
// 它提供了 addComponent、loadLayout、saveLayout 等方法
let vglLayout: VirtualLayout
// vglLayoutState: 存储布局的状态信息（如当前聚焦的组件等）
const vglLayoutState = ref<VglLayoutState>({ focus: null })

// vglRoot: Golden Layout 的根 DOM 元素引用
// Golden Layout 会在这个容器内创建布局结构（拖拽条、标签页等）
const vglRoot = useTemplateRef<HTMLElement>('vglRoot')

// VGL_COMPONENT_REF_PREFIX: Vue ref 的命名前缀
// 用于生成唯一的 ref 名称，如 'vglc_0', 'vglc_1', 'vglc_2'
// 这样可以通过 instance.refs['vglc_0'] 访问到对应的组件实例
const VGL_COMPONENT_REF_PREFIX = readonly(ref<string>('vglc_'))

// containerComponentMapper: Golden Layout 容器 ↔ Vue 组件实例 的映射表
// 当 Golden Layout 触发事件时（如调整大小），通过这个 Map 找到对应的 Vue 组件进行操作
// 键：ComponentContainer（Golden Layout 创建的虚拟容器）
// 值：ResolvedVglComponentInfo（包含 refId 和组件实例）
const containerComponentMapper = new Map<ComponentContainer, ResolvedVglComponentInfo>()

// refIdItemMapper: refId → ComponentItem 的映射表
// 用于快速通过 refId 获取 ComponentItem，以便调用 focusComponent 等方法
// 键：refId（数字索引）
// 值：ComponentItem（Golden Layout 的组件项）
const refIdItemMapper = new Map<number, ComponentItem>()

// refIdComponentMapper: refId → { component, state } 的映射表
// 这是一个响应式 Map，当修改它时会触发模板重新渲染
// 键：refId（数字索引）
// 值：{ component: Vue组件构造函数, state: componentState }
const refIdComponentMapper = ref(new Map<number, { component: any; state: any }>())

// onTabCloseCallback: 标签页关闭时的回调函数
// 在 unbindComponentEventListener 中触发
let onTabCloseCallback: ((refId: number, componentState: any) => void) | null = null

// tabTemplates: 预收集所有 TabTemplate 组件的模块映射
// 使用 import.meta.glob 让 Vite 在构建时静态分析，确保生产包中包含所有模板
const tabTemplates = import.meta.glob('./TabTemplates/*.vue')

// unusedIndexes: 回收的索引池
// 当组件被删除时，它的 refId 会被放入这个数组，供下次复用
// 这样可以避免索引无限增长，提高内存利用率
const unusedIndexes: number[] = []

// currIndex: 当前最大索引值
// 每次创建新组件时，如果没有可复用的索引，就使用这个值并自增
let currIndex = 0

// vglBoundingClientRect: Golden Layout 根容器的边界矩形
// 用于计算子组件相对于根容器的坐标位置
// 在 handleBeforeVirtualRectingEvent 中更新
let vglBoundingClientRect: DOMRect

// instance: 当前组件实例的引用
// 通过它可以访问 Vue 的 refs、props、emit 等
const instance = getCurrentInstance()

/**
 * 组件方法
 */

/**
 * 【内部方法】添加组件到映射表
 *
 * 这个方法负责：
 * 1. 从预加载的模块中查找对应组件
 * 2. 分配一个唯一的 refId
 * 3. 将组件构造函数存入 refIdComponentMapper
 * 4. 返回 refId 供后续使用
 *
 * @param componentType 组件名称（不含 .vue 后缀），如 'ChartPanel'
 * @param _title 标签页标题（此处未使用，但保留参数以保持接口一致）
 * @param componentState 传递给组件的状态数据（可选）
 * @returns refId - 分配给组件的唯一索引
 *
 * 工作原理：
 * - 在预加载的 panelModules 中查找匹配的组件
 * - 使用模块的动态导入函数创建异步组件
 * - markRaw() 标记为非响应式，避免不必要的性能开销
 */
const _addComponent = (componentType: string, _title: string, componentState?: any) => {
  // 从预收集的模块映射中查找组件，而非动态 import()
  const component = markRaw(
    defineAsyncComponent(async () => {
      const path = `./TabTemplates/${componentType}.vue`
      const loader = tabTemplates[path]
      if (!loader) throw new Error(`Template not found: ${path}`)
      const mod = await loader() as { default: any }
      return mod.default
    })
  )

  // 分配 refId：优先复用已删除组件的索引，否则使用新索引
  let index = currIndex
  if (unusedIndexes.length > 0) {
    index = unusedIndexes.pop() as number // 从回收池取出
  } else {
    currIndex++ // 使用新索引并递增
  }

  // 存入映射表：refId → { component, state }
  // 这会触发 Vue 的响应式更新，模板中的 v-for 会重新渲染
  refIdComponentMapper.value.set(index, { component: component, state: componentState })

  return index
}

/**
 * 【公开方法】动态添加单个组件到布局中
 *
 * 使用场景：
 * - 用户点击按钮添加新面板
 * - 程序化创建组件
 * - 打开路由页面
 *
 * 与 loadLayout 的区别：
 * - addComponent：添加单个组件到现有布局
 * - loadLayout：加载完整布局配置（会清空现有布局）
 *
 * @param componentType 组件名称，如 'ChartPanel' 或 'RouterPanel'
 * @param title 标签页显示的标题
 * @param componentState 传递给组件的状态数据（可选）
 *                       例如：{ routePath: '/dashboard', userId: 123 }
 *
 * 执行流程：
 * 1. 调用 _addComponent 创建组件并分配 refId
 * 2. await nextTick() 等待 Vue 渲染 DOM
 * 3. 调用 vglLayout.addComponent 通知 Golden Layout
 * 4. Golden Layout 会触发 bindComponentEventListener 建立绑定
 */
const addComponent = async (componentType: string, title: string, componentState?: Record<string, any>) => {
  if (componentType.length === 0) throw new Error("VGL-addComponent: Component's type is empty")

  // 传递 componentState 给 _addComponent，用于存储到 refIdComponentMapper
  const index = _addComponent(componentType, title, componentState)

  await nextTick() // 等待 Vue 完成 DOM 更新

  // 合并 refId 和自定义 componentState
  const state = { refId: index, ...componentState }
  vglLayout.addComponent(componentType, state, title)

  return index
}

/**
 * 加载布局配置
 * @param layoutConfig 布局配置
 */
const loadLayout = async (layoutConfig: LayoutConfig | ResolvedLayoutConfig) => {
  vglLayout.clear()
  refIdComponentMapper.value.clear()

  const config = (
    'resolved' in layoutConfig && layoutConfig?.resolved // 如果是 ResolvedLayoutConfig 类型且 resolved 字段为 true
      ? LayoutConfig.fromResolved(layoutConfig)
      : layoutConfig
  ) as LayoutConfig

  if (!config.root?.content) {
    throw new Error('loadLayout: Invalid layout config')
  }

  /**
   * 使用 BFS（广度优先搜索）遍历布局配置树，预先添加所有 component
   *
   * 布局结构示例：
   * ```
   * root
   *  └─ content: [row, stack, component]           ← 第一层（根节点的直接子节点）
   *       ├─ row.content: [component, component]   ← 第二层（row 的子节点）
   *       └─ stack.content: [component]            ← 第二层（stack 的子节点）
   * ```
   *
   * contents 是一个队列，存储"待处理的配置数组"：
   * - 初始化时放入根节点的 content（第一层）
   * - 每次循环从队列头部取出一个数组进行处理
   * - 如果发现某个配置项还有子节点，就把子节点数组加入队列尾部
   * - 这样可以逐层处理，确保父容器先于子组件被处理
   */
  const contents: AnyItemConfig[][] = [
    config.root.content as AnyItemConfig[], // 初始化：放入第一层配置
  ]

  let index = 0
  while (contents.length > 0) {
    // 从队列头部取出一层的所有配置项
    const content = contents.shift() as AnyItemConfig[]

    // 遍历当前层的每个配置项
    for (const itemConfig of content) {
      if (itemConfig.type === 'component') {
        // 1. 获取现有的 componentState（可能包含路由信息等）
        const existingState = itemConfig.componentState ?? {}

        // 2. 如果是叶子节点（component），创建组件实例，传入 componentState
        index = _addComponent(
          itemConfig.componentType as string,
          itemConfig.title as string,
          existingState // 传递 componentState 给 _addComponent
        )
        // ↑ _addComponent 内部会执行：refIdComponentMapper.value.set(index, { component, state })
        //   refIdComponentMapper 是响应式的 ref，修改它会触发 Vue 的更新队列

        // 3. 在配置中注入 refId，用于后续绑定 Vue 组件引用
        if (itemConfig?.componentState !== undefined) {
          itemConfig.componentState['refId'] = index
        } else {
          itemConfig.componentState = { refId: index }
        }
      } else if (itemConfig.content.length > 0) {
        // 3. 如果是容器节点（row/column/stack）且有子节点，
        //    把子节点数组加入队列，等待后续处理
        contents.push(itemConfig.content as AnyItemConfig[])
      }
    }
  }

  // 【关键】等待 Vue 完成 DOM 更新
  // 前面的循环修改了 refIdComponentMapper（响应式数据），触发了模板中的 v-for 重新渲染
  // 模板：<gl-component v-for="pair in refIdComponentMapper" ...>
  // nextTick 确保所有新的 <gl-component> DOM 元素都已创建并挂载到页面上
  // vglLayout.loadLayout 需要通过 ref 访问这些 DOM 元素，所以必须等待 DOM 更新完成
  await nextTick()

  vglLayout.loadLayout(config)
}

const getLayoutConfig = () => {
  return vglLayout.saveLayout()
}

/**
 * 【公开方法】激活指定的标签页
 *
 * 使用场景：
 * - 路由变化时，激活对应的已打开标签页
 * - 用户点击菜单时，切换到已存在的标签页
 *
 * @param refId 标签页的 refId（存储在 componentState 中）
 * @returns 是否成功激活（如果标签页不存在则返回 false）
 */
const activateTabByRefId = (refId: number): boolean => {
  if (!vglLayout) return false

  // 从映射表中获取 ComponentItem
  const item = refIdItemMapper.get(refId)
  if (item) {
    // 使用 Golden Layout 官方 API 聚焦组件
    vglLayout.focusComponent(item, false)
    console.log('[VGL] 激活标签页:', refId, item.toConfig().title)
    return true
  }
  console.warn('[VGL] 标签页不存在:', refId)
  return false
}

/**
 * 【公开方法】获取当前激活的标签页信息
 * 用于路由同步
 */
const getActiveTab = (): any => {
  const item = vglLayoutState.value.focus
  if (!item) return null

  // 从 ComponentItem 的配置中获取 componentState
  const config = item.toConfig()
  return config.componentState || null
}

const registerOnFocusCallback = (callback: (componentState: ResolvedVglComponentInfo) => void) => {
  const innerCallback = (event: any) => {
    callback(containerComponentMapper.get(event.target.container) as ResolvedVglComponentInfo)
  }
  vglLayout.on('focus', innerCallback as any)
}

/**
 * 【公开方法】注册标签页关闭回调
 *
 * 使用场景：
 * - 同步更新路由状态
 * - 清理标签页记录
 *
 * @param callback 回调函数，参数为被关闭标签页的 refId 和 componentState
 */
const registerOnTabCloseCallback = (callback: (refId: number, componentState: any) => void) => {
  onTabCloseCallback = callback
}

/**
 * 生命周期函数
 * - onMounted：组件挂载完成后初始化 Golden Layout
 */
onMounted(() => {
  if (vglRoot.value == null) throw new Error("Golden Layout can't find the root DOM!")

  /**
   * 使用 ResizeObserver 监听容器尺寸变化（替代 window resize）
   * 更精确且避免 ResizeObserver 循环警告
   */
  let resizeObserver: ResizeObserver | null = null

  const updateSize = () => {
    const dom = vglRoot.value
    if (dom) {
      vglLayout.setSize(dom.offsetWidth, dom.offsetHeight)
    }
  }

  // 使用 ResizeObserver 直接监听根容器尺寸变化
  resizeObserver = new ResizeObserver(() => {
    // 使用 requestAnimationFrame 避免频繁更新
    requestAnimationFrame(updateSize)
  })

  resizeObserver.observe(vglRoot.value)

  /**
   * 在每次布局重新计算前，获取根容器的边界矩形（注册layout回调）
   * 这样子组件在计算自己的位置时，可以基于根容器的坐标系进行计算
   * 例如，子组件的 left = 子组件的 left - 根容器的 left
   * 这样可以确保子组件在根容器内正确定位
   * @param _count 重新计算的次数
   */
  const handleBeforeVirtualRectingEvent = (_count: number) => {
    vglBoundingClientRect = (vglRoot.value as HTMLElement).getBoundingClientRect()
  }

  /**
   * 处理容器的虚拟矩形变更事件（注册layout回调）
   * 例如，当容器大小或位置发生变化时，Golden Layout 会触发此事件
   * 组件需要根据新的宽高调整自己的位置和尺寸
   * @param container 虚拟容器
   * @param width 变化后的宽度
   * @param height 变化后的高度
   */
  const handleContainerVirtualRectingRequiredEvent = (
    container: ComponentContainer,
    width: number,
    height: number
  ): void => {
    const component = containerComponentMapper.get(container)
    if (!component || !component?.vglComponent) {
      throw new Error('handleContainerVirtualRectingRequiredEvent: Component not found')
    }
    const containerBoundingClientRect = container.element.getBoundingClientRect()
    const left = containerBoundingClientRect.left - vglBoundingClientRect.left
    const top = containerBoundingClientRect.top - vglBoundingClientRect.top
    component.vglComponent.setPosAndSize(left, top, width, height)
  }

  /**
   * 处理容器的虚拟可见性变更事件（注册layout回调）
   * 例如，当容器被隐藏或显示时，Golden Layout 会触发此事件
   * 组件需要根据可见性状态调整自己的显示或隐藏
   * @param container 虚拟容器
   * @param visible 变化后的可见性状态
   */
  const handleContainerVirtualVisibilityChangeRequiredEvent = (
    container: ComponentContainer,
    visible: boolean
  ): void => {
    const component = containerComponentMapper.get(container)
    if (!component || !component?.vglComponent) {
      throw new Error('handleContainerVirtualVisibilityChangeRequiredEvent: Component not found')
    }
    component.vglComponent.setVisibility(visible)
  }

  /**
   * 处理容器的虚拟ZIndex变更事件（注册layout回调）
   * 例如，当容器的层级关系发生变化时，Golden Layout 会触发此事件
   * 组件需要根据新的ZIndex调整自己的层级显示
   * @param container 虚拟容器
   * @param _logicalZIndex 逻辑ZIndex
   * @param defaultZIndex 变化后的默认ZIndex
   */
  const handleContainerVirtualZIndexChangeRequiredEvent = (
    container: ComponentContainer,
    _logicalZIndex: LogicalZIndex,
    defaultZIndex: string
  ): void => {
    const component = containerComponentMapper.get(container)
    if (!component || !component?.vglComponent) {
      throw new Error('handleContainerVirtualZIndexChangeRequiredEvent: Component not found')
    }
    component.vglComponent.setZIndex(defaultZIndex)
  }

  /**
   * 【核心回调】绑定组件的事件监听器
   *
   * 这个函数在 Golden Layout 加载配置时被调用，用于建立 Golden Layout 容器与 Vue 组件之间的桥梁
   *
   * 调用时机：
   * - vglLayout.loadLayout(config) 内部会遍历所有 component 配置
   * - 对每个 component，Golden Layout 会调用这个回调函数
   *
   * 工作流程：
   * 1. 从配置中提取 refId（我们在 loadLayout 中注入的）
   * 2. 使用 refId 从 Vue 的 refs 中找到对应的组件实例
   * 3. 建立映射关系：Golden Layout 容器 → Vue 组件实例
   * 4. 为容器注册事件监听器，让 Golden Layout 能够控制 Vue 组件
   * 5. 返回绑定结果给 Golden Layout
   *
   * @param container Golden Layout 创建的虚拟容器（用于管理布局）
   * @param itemConfig 组件的配置信息（包含我们注入的 refId）
   * @returns 返回绑定信息，告诉 Golden Layout 这是一个虚拟组件
   */
  const bindComponentEventListener = (
    container: ComponentContainer,
    itemConfig: ResolvedComponentItemConfig
  ): ComponentContainer.BindableComponent => {
    // 步骤 1：从配置中提取 refId
    let refId = -1
    if (itemConfig && itemConfig.componentState) {
      // componentState 是我们在 loadLayout 中注入的 { refId: xxx }
      refId = (itemConfig.componentState as Json).refId as number
    } else {
      // 如果没有 refId，说明配置有问题，抛出错误
      throw new Error("bindComponentEventListener: component's ref id is required")
    }

    // 步骤 2：构造 Vue ref 的名称并获取组件实例
    const ref = VGL_COMPONENT_REF_PREFIX.value + refId // 例如：'vglc_0', 'vglc_1', 'vglc_2'

    // Vue 3 的 refs 行为：
    // - 在 v-for 中使用 :ref="xxx" 时，instance.refs[xxx] 返回的是数组
    // - 即使只有一个元素，也是 [component] 而不是 component
    const componentArr = instance?.refs[ref] as any[] | any
    const component = Array.isArray(componentArr) ? componentArr[0] : componentArr

    // 【调试】打印组件引用信息
    console.log('[VGL Debug] bindComponentEventListener:', {
      refId,
      refName: ref,
      componentArr,
      component,
      allRefs: Object.keys(instance?.refs || {}),
    })

    // 步骤 3：确保组件存在（防止空引用错误）
    if (!component) {
      console.error('[VGL Error] Component not found:', {
        refId,
        refName: ref,
        availableRefs: Object.keys(instance?.refs || {}),
        refIdComponentMapper: Array.from(refIdComponentMapper.value.keys()),
      })
      throw new Error(`bindComponentEventListener: Component with ref "${ref}" not found`)
    }

    // 步骤 4：建立映射关系
    // 将 Golden Layout 的容器对象与 Vue 组件实例关联起来
    // 后续当 Golden Layout 触发事件时，我们可以通过容器找到对应的 Vue 组件
    containerComponentMapper.set(container, {
      refId: refId,
      vglComponent: component,
      vglComponentState: itemConfig.componentState,
    })

    // 步骤 4.5：建立 refId → ComponentItem 映射
    // container.parent 就是 ComponentItem，用于后续调用 focusComponent 等方法
    const componentItem = container.parent
    refIdItemMapper.set(refId, componentItem)

    // 【调试】打印映射信息
    console.log('[VGL Debug] ComponentItem 映射:', {
      refId,
      componentItem,
    })

    // 步骤 5：为容器注册事件监听器
    // 当 Golden Layout 需要改变组件的位置、大小、可见性、层级时，会触发这些事件

    // 当布局需要重新计算组件的位置和大小时触发
    container.virtualRectingRequiredEvent = (container, width, height) =>
      handleContainerVirtualRectingRequiredEvent(container, width, height)

    // 当组件需要显示或隐藏时触发
    container.virtualVisibilityChangeRequiredEvent = (container, visible) =>
      handleContainerVirtualVisibilityChangeRequiredEvent(container, visible)

    // 当组件的层级（z-index）需要改变时触发
    container.virtualZIndexChangeRequiredEvent = (container, logicalZIndex, defaultZIndex) =>
      handleContainerVirtualZIndexChangeRequiredEvent(container, logicalZIndex, defaultZIndex)

    // 步骤 6：返回绑定结果
    return {
      component, // 返回组件实例给 Golden Layout
      virtual: true, // 标记为虚拟组件（不使用 iframe，直接渲染在页面上）
    }
  }

  /**
   * 【核心回调】解绑组件的事件监听器
   *
   * 调用时机：
   * - 用户关闭标签页
   * - 调用 vglLayout.clear() 清空布局
   * - 布局重新加载
   *
   * 工作流程：
   * 1. 从 containerComponentMapper 中查找要删除的组件
   * 2. 从映射表中删除该组件
   * 3. 将 refId 放入回收池
   * 4. 清理 refIdComponentMapper（触发 Vue 销毁组件）
   *
   * @param container 要解绑的 Golden Layout 容器
   *
   * 资源回收：
   * - containerComponentMapper.delete() → 断开 Golden Layout ↔ Vue 的连接
   * - refIdComponentMapper.delete() → 触发 Vue 销毁组件实例
   * - unusedIndexes.push() → 回收 refId，供下次复用
   */
  const unbindComponentEventListener = (container: ComponentContainer): void => {
    // 步骤 1：查找要删除的组件
    const component = containerComponentMapper.get(container)
    if (!component || !component?.vglComponent) {
      throw new Error('handleUnbindComponentEvent: Component not found')
    }

    // 步骤 1.5：在清理映射表之前，触发标签页关闭回调
    // 此时 component.vglComponentState 还存在，可以传递给外部
    if (onTabCloseCallback) {
      console.log('[VGL] 标签页已关闭:', component.refId)
      onTabCloseCallback(component.refId, component.vglComponentState)
    }

    // 步骤 2：删除映射关系
    containerComponentMapper.delete(container)

    // 步骤 2.5：删除 refId → ComponentItem 映射
    refIdItemMapper.delete(component.refId)

    // 步骤 3：从组件映射表中删除（触发 Vue 响应式更新，销毁组件）
    refIdComponentMapper.value.delete(component.refId)

    // 步骤 4：将 refId 放入回收池，供下次创建组件时复用
    unusedIndexes.push(component.refId)

    // 【调试】打印解绑信息
    console.log('[VGL Debug] ComponentItem 解绑:', {
      refId: component.refId,
      remainingMappings: refIdItemMapper.size,
    })
  }

  vglLayout = new VirtualLayout(vglRoot.value, bindComponentEventListener, unbindComponentEventListener)

  vglLayout.beforeVirtualRectingEvent = handleBeforeVirtualRectingEvent

  // 监听 focus 事件，更新 vglLayoutState
  vglLayout.on('focus', ((event: any) => {
    vglLayoutState.value.focus = event.target
    // 【调试】打印焦点变化
    console.log('[VGL Debug] Focus 事件:', {
      focusTitle: (event.target as ComponentItem)?.toConfig()?.title,
      focusType: (event.target as ComponentItem)?.type,
    })
  }) as any)

  // 清理函数：在组件卸载时移除监听器
  onBeforeUnmount(() => {
    if (resizeObserver) {
      resizeObserver.disconnect()
      resizeObserver = null
    }
  })
})

/**
 * 公开外部可调用的方法
 */
defineExpose({
  addComponent,
  loadLayout,
  getLayoutConfig,
  activateTabByRefId,
  getActiveTab,
  registerOnFocusCallback,
  registerOnTabCloseCallback,
})
</script>

<template>
  <div class="relative">
    <div ref="vglRoot" class="absolute w-full h-full">
      <!-- Root dom for Golden-Layout manager -->
    </div>
    <div class="absolute w-full h-full">
      <GlComponentWrapper
        v-for="[refId, { component, state }] in refIdComponentMapper"
        :key="refId"
        :ref="VGL_COMPONENT_REF_PREFIX + refId"
      >
        <component :is="component" v-bind="state" />
      </GlComponentWrapper>
    </div>
  </div>
</template>

<style scoped></style>

