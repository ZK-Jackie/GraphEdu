/**
 * 路由工具函数
 *
 * 功能：
 * 1. 将后端 FunctionTreeVO 转换为 Ant Design Menu ItemType
 * 2. 将后端 FunctionTreeVO 转换为 Vue Router RouteRecordRaw
 * 3. 菜单激活状态管理
 * 4. 路由匹配和查找
 */
import { h } from 'vue'
import type { FunctionTreeVO } from '@/types/api/system/function.ts'
import type { ItemType } from 'ant-design-vue'
import type {
  MenuDividerType,
  MenuItemType,
  MenuItemGroupType,
  SubMenuType,
} from 'ant-design-vue/es/menu/src/hooks/useItems'
import type { RouteRecordRaw, RouteLocationMatched } from 'vue-router'
import SvgIcon from '@/components/SvgIcon/index.vue'

const allViews = import.meta.glob('../views/**/*.vue')
const allLayouts = import.meta.glob('../layout/**/*.vue')

/** 功能类型到菜单类型的映射 */
const FUNCTION_TYPE_TO_MENU_TYPE: Record<string, 'menu' | 'item' | 'group' | 'divider'> = {
  DIR: 'menu', // 目录 -> 子菜单
  MENU: 'item', // 菜单 -> 菜单项
  GROUP: 'group', // 分组 -> 菜单分组
  DIVIDER: 'divider', // 分隔线 -> 菜单分隔线
  // BUTTON 和 INTERFACE 不在菜单中显示
}

/**
 * 递归清理菜单项：移除 children 为空的子菜单和分组
 * 防止 Ant Design Vue InternalSubMenuList 渲染空子菜单时报错
 */
function sanitizeMenuItems(items: ItemType[]): ItemType[] {
  return items.filter((item) => {
    if (!item) return false
    const it = item as any
    // 分组 / 子菜单如果有 children，递归清理后若为空则移除
    if (Array.isArray(it.children)) {
      it.children = sanitizeMenuItems(it.children)
      if (it.children.length === 0) return false
    }
    return true
  })
}

/**
 * 将 FunctionTreeVO 转换为 Ant Design Menu
 *
 * @param functionTreeList - 后端返回的功能树列表
 * @returns Ant Design Menu 可用的菜单项数组
 */
export function transformFunctionToMenu(functionTreeList: FunctionTreeVO[]): ItemType[] {
  const menuItems: ItemType[] = []

  for (const func of functionTreeList) {
    // 跳过隐藏和停用的功能
    if (func.visible === 'N' || func.status === '1') {
      continue
    }

    const menuType = FUNCTION_TYPE_TO_MENU_TYPE[func.functionType]

    // 跳过不支持的类型（BUTTON, INTERFACE等）
    if (!menuType) {
      continue
    }

    // 根据类型生成不同的菜单项
    switch (menuType) {
      case 'divider':
        menuItems.push({
          type: 'divider',
          dashed: func.optionStyle?.dashed === true,
          style: func.style,
        } as MenuDividerType)
        break

      case 'group': {
        const groupChildren = func.children ? transformFunctionToMenu(func.children) : []
        if (groupChildren.length === 0) break
        menuItems.push({
          type: 'group',
          label: func.functionName,
          children: groupChildren,
          style: func.style as Record<string, string>,
        } as MenuItemGroupType)
        break
      }

      case 'menu': {
        // 目录类型：有子菜单则渲染为子菜单，无子菜单则降级为可点击菜单项
        const childItems = func.children ? transformFunctionToMenu(func.children) : []
        if (childItems.length === 0) {
          menuItems.push({
            label: func.functionName,
            key: func.functionKey,
            icon: func.icon ? getIconVNode(func.icon) : undefined,
            style: func.style,
            disabled: func.optionStyle?.disabled === true,
            path: func.routePath,
          } as MenuItemType)
        } else {
          menuItems.push({
            label: func.functionName,
            key: func.functionKey,
            icon: func.icon ? getIconVNode(func.icon) : undefined,
            children: childItems,
            style: func.style,
            disabled: func.optionStyle?.disabled === true,
          } as SubMenuType)
        }
        break
      }

      case 'item':
        // 菜单项类型：可点击跳转的叶子节点
        menuItems.push({
          label: func.functionName,
          key: func.functionKey,
          icon: func.icon ? getIconVNode(func.icon) : undefined,
          style: func.style,
          disabled: func.optionStyle?.disabled === true,
          danger: func.optionStyle?.danger === true,
          path: func.routePath,
        } as MenuItemType)
        break
    }
  }

  return sanitizeMenuItems(menuItems)
}

/** 场景类型 */
type SceneType = 'web' | 'admin' | 'mobile' | 'userInfo'

/**
 * 判断功能节点是否应被跳过
 * @param func 功能节点
 * @returns 是否跳过
 */
function shouldSkipFunction(func: FunctionTreeVO): boolean {
  // 只处理目录和菜单类型
  if (!['DIR', 'MENU'].includes(func.functionType)) {
    return true
  }
  // 跳过停用的功能
  return func.status === '1'
}

/**
 * 获取场景的默认布局组件
 * @param scene 场景类型
 * @returns 默认布局组件或 undefined
 */
function getDefaultLayoutForScene(scene: SceneType): any {
  switch (scene) {
    case 'admin':
      return () => import('@/layout/WorkbenchLayout/index.vue')
    // case 'mobile':
    // TODO return () => import('@/layout/MobileLayout/index.vue')
    // web 和 userInfo 场景默认不使用布局
    // eslint-disable-next-line no-fallthrough
    case 'web':
      return () => import('@/layout/CommonLayout/index.vue')
    case 'userInfo':
    default:
      return undefined
  }
}

/**
 * 根据路径获取布局组件
 * @param path 布局组件路径
 * @returns 布局组件或 undefined
 */
function getLayoutComponentWithPath(path: string): any {
  if (!path || path.trim() === '') {
    return undefined
  }

  // 规范化路径：去除前导斜杠和 .vue 后缀
  let normalizedPath = path.replace(/^\//, '').replace(/\.vue$/, '')

  // 如果路径以 'layout/' 开头，去掉这个前缀（避免路径重复）
  if (normalizedPath.startsWith('layout/')) {
    normalizedPath = normalizedPath.replace(/^layout\//, '')
  }

  const componentPath = `../layout/${normalizedPath}.vue`
  const component = allLayouts[componentPath]

  if (!component) {
    return undefined
  }

  return component
}

/**
 * 构建路由 meta 对象
 * @param func 功能节点
 * @param scene 场景类型
 * @returns 路由 meta 对象
 */
function buildRouteMeta(func: FunctionTreeVO, scene: SceneType): RouteRecordRaw['meta'] {
  return {
    title: func.functionName,
    key: func.functionKey,
    icon: func.icon,
    keepAlive: func.routeCache === '1',
    link: func.routeExternal === '1' ? func.routePath : undefined,
    hidden: func.visible === 'N',
    enabled: func.status === '0',
    order: func.sortOrder,
    style: func.style,
    optionStyle: func.optionStyle,
    dynamic: true,
    scene: scene,
    layoutComponent: func.layoutComponent,
    query: func.routeQuery,
  }
}

/**
 * 解析布局组件
 *
 * 优先级：
 * 1. 节点指定的 layoutComponent（使用自己的布局）
 * 2. DIR 类型：根据场景使用默认布局（必须有布局）
 * 3. MENU 类型：不返回布局（由父路由处理）
 *
 * @param func 功能节点
 * @returns 布局组件或 undefined
 */
function resolveLayoutComponent(func: FunctionTreeVO): any {
  const scene = (func.scene || 'web') as SceneType

  // 1. 如果当前节点指定了 layoutComponent，使用自己的布局
  if (func.layoutComponent) {
    const layout = getLayoutComponentWithPath(func.layoutComponent)
    if (layout) {
      return layout
    }
  }

  // 2. DIR 类型：必须有布局组件，使用默认布局
  if (func.functionType === 'DIR') {
    const defaultLayout = getDefaultLayoutForScene(scene)
    if (defaultLayout) {
      return defaultLayout
    }
  }

  // 3. MENU 类型：不返回布局（将作为父路由的子路由）
  return undefined
}

/**
 * 计算子路由的相对路径
 * 优先通过剥去父路径前缀得到多段相对路径（如 course/:courseId），
 * 若子路径不以父路径开头则回退为最后一段。
 */
function getRelativePath(childPath: string, parentPath: string): string {
  const normalizedParent = parentPath.replace(/\/$/, '')
  const normalizedChild = childPath.startsWith('/') ? childPath : `/${childPath}`
  if (normalizedChild.startsWith(`${normalizedParent}/`)) {
    return normalizedChild.slice(normalizedParent.length + 1)
  }
  // 回退：取最后一段
  const segments = normalizedChild.split('/').filter(Boolean)
  return segments[segments.length - 1] ?? ''
}

/**
 * 处理有子路由的节点（DIR 类型）
 * @param route 路由对象
 * @param func 功能节点
 * @param layout 当前节点的布局组件
 * @param absolutePath 当前节点的完整路径（用于计算子路由的相对路径）
 */
function handleRouteWithChildren(route: any, func: FunctionTreeVO, layout: any, absolutePath: string): void {
  // DIR 节点必须有布局组件
  if (!layout) {
    const scene = (func.scene || 'web') as SceneType
    layout = getDefaultLayoutForScene(scene)
  }

  // 设置布局组件
  route.component = layout

  // 递归处理子路由（子路由路径相对于当前路由）
  console.log(
    `[Router Utils] handleRouteWithChildren: 处理 ${func.functionKey} 的子路由，共 ${func.children?.length ?? 0} 个`
  )
  const childRoutes = transformFunctionToRoute(func.children ?? [], absolutePath)
  console.log(
    `[Router Utils] handleRouteWithChildren: ${func.functionKey} 转换后得到 ${childRoutes.length} 个子路由`,
    childRoutes.map((c) => ({ name: c.name, path: c.path, hasComponent: !!c.component }))
  )

  // 如果 DIR 节点有自己的 component，创建嵌套结构
  if (func.component) {
    const viewComponent = getViewComponent(func.component)
    if (viewComponent) {
      // 创建空路径子路由，作为容器包含其他子路由
      const indexRoute: any = {
        path: '',
        name: `${func.functionKey}_index`,
        component: viewComponent,
        meta: route.meta,
      }

      // 如果有子路由，将它们嵌套在空路径子路由中
      if (childRoutes.length > 0) {
        indexRoute.children = childRoutes
        // 设置重定向到第一个可见的子路由
        const firstChild = childRoutes.find((child: any) => !child.meta?.hidden)
        if (firstChild) {
          indexRoute.redirect = { name: firstChild.name as string }
        }
      }

      route.children = [indexRoute]
    } else {
      // component 无效，回退到默认行为
      route.children = childRoutes
      if (childRoutes.length > 0) {
        const firstChild = childRoutes.find((child: any) => !child.meta?.hidden)
        if (firstChild) {
          route.redirect = { name: firstChild.name as string }
        }
      }
    }
  } else {
    // DIR 节点没有 component，子路由直接作为父路由的 children（原有行为）
    route.children = childRoutes
    if (childRoutes.length > 0) {
      const firstChild = childRoutes.find((child: any) => !child.meta?.hidden)
      if (firstChild) {
        route.redirect = { name: firstChild.name as string }
      }
    }
  }

  console.log(
    `[Router Utils] handleRouteWithChildren: ${func.functionKey} 最终的 children:`,
    route.children?.map((c: any) => ({ name: c.name, path: c.path, hasComponent: !!c.component }))
  )
}

/**
 * 处理叶子节点（MENU 类型，无子路由）
 * @param route 路由对象
 * @param func 功能节点
 * @param layout 布局组件（如果有自己的布局）
 * @param viewComponent 视图组件
 */
function handleLeafRoute(route: any, func: FunctionTreeVO, layout: any, viewComponent: any): void {
  if (!viewComponent) {
    console.warn(`[Router Utils] handleLeafRoute: 组件为空 - name: ${func.functionKey}, component: ${func.component}`)
  }

  if (layout) {
    // MENU 有自己的布局组件：创建嵌套结构
    // 这种情况适用于：需要特殊布局的页面（如 dashboard）
    route.component = layout
    route.children = [
      {
        path: '',
        name: `${func.functionKey}_content`,
        component: viewComponent,
        meta: route.meta,
      },
    ]
  } else if (viewComponent) {
    // MENU 没有自己的布局：直接使用页面组件
    // 这种情况适用于：在父路由的布局中显示的普通页面
    route.component = viewComponent
  }

  console.log(
    `[Router Utils] handleLeafRoute: name=${func.functionKey}, path=${route.path}, hasComponent=${!!route.component}`
  )
}

/**
 * 将 FunctionTreeVO 转换为 Vue Router 的 RouteRecordRaw
 *
 * 功能类型映射：
 * - DIR: 生成父级路由，有 children。必须有 layoutComponent，定义其下组件使用的布局
 * - MENU: 生成可访问的页面路由。可选择定义 layoutComponent（嵌套布局）或作为父路由的子路由
 *
 * 布局嵌套规则：
 * 1. DIR 节点必须有 layoutComponent（否则使用默认布局）
 * 2. DIR 节点的子路由作为其 children，路径为相对路径
 * 3. MENU 节点如果有自己的 layoutComponent，创建嵌套布局结构
 * 4. MENU 节点如果没有 layoutComponent，直接作为父路由的子路由
 *
 * @param functionTreeList - 后端返回的 FunctionTreeVO 列表
 * @param parentPath - 父路由的完整绝对路径（留空时处理顶层路由）
 * @returns Vue Router 可用的路由配置
 */
export function transformFunctionToRoute(
  functionTreeList: FunctionTreeVO[],
  parentPath: string = ''
): RouteRecordRaw[] {
  const routes: RouteRecordRaw[] = []

  for (const func of functionTreeList) {
    // 过滤不需要处理的节点
    if (shouldSkipFunction(func)) {
      continue
    }

    const scene = (func.scene || 'web') as SceneType

    // 处理路由路径
    let routePath = func.routePath?.trim() ? func.routePath : `/${func.functionKey}`

    // 规范化路径：
    // - 子路由使用相对路径（剥去父路径前缀，支持多段路径如 course/:courseId）
    // - 根路由使用绝对路径（保留前导斜杠）
    if (parentPath) {
      routePath = getRelativePath(routePath, parentPath)
    } else if (!routePath.startsWith('/')) {
      routePath = `/${routePath}`
    }

    // 计算当前节点的完整路径，用于子路由的相对路径计算
    const absolutePath = parentPath ? `${parentPath.replace(/\/$/, '')}/${routePath}` : routePath

    // 解析布局组件
    const layoutComponent = resolveLayoutComponent(func)

    // 获取视图组件
    const viewComponent = getViewComponent(func.component)

    // 构建基础路由对象
    const route: any = {
      path: routePath,
      name: func.functionKey,
      meta: buildRouteMeta(func, scene),
    }

    // 根据是否有子路由分别处理
    if (func.children && func.children.length > 0) {
      // 有子路由：DIR 类型的父级路由
      handleRouteWithChildren(route, func, layoutComponent, absolutePath)
    } else {
      // 叶子节点：MENU 类型的页面路由
      handleLeafRoute(route, func, layoutComponent, viewComponent)
    }

    routes.push(route)
  }

  return routes
}

/**
 * 根据路径动态获取视图组件
 * @param path 视图组件路径，支持以下格式：
 *   - 相对于 views 目录：'system/user/index' 或 'dashboard/Analysis'
 *   - 从 src 目录开始：'views/system/user/index'
 *   - 带前导斜杠：'/views/system/user/index'
 * @returns 视图组件或 undefined
 */
export function getViewComponent(path: string | undefined) {
  if (!path || path.trim() === '') {
    console.warn('[Router Utils] getViewComponent: 路径为空')
    return undefined
  }

  // 规范化路径：去除前导斜杠和 .vue 后缀
  let normalizedPath = path.replace(/^\//, '').replace(/\.vue$/, '')

  // 如果路径以 'views/' 开头，去掉这个前缀（避免路径重复）
  if (normalizedPath.startsWith('views/')) {
    normalizedPath = normalizedPath.replace(/^views\//, '')
  }

  const componentPath = `../views/${normalizedPath}.vue`

  const component = allViews[componentPath]

  if (!component) {
    console.warn(`[Router Utils] getViewComponent: 组件未找到 - path: ${path}, componentPath: ${componentPath}`)
    console.log(
      '[Router Utils] 可用的组件路径:',
      Object.keys(allViews).filter((k) => k.includes('learn'))
    )
    return undefined
  }

  return component
}

/**
 * 创建图标虚拟节点
 * @param iconString 图标名称
 * @returns 图标虚拟节点
 */
export function getIconVNode(iconString: string) {
  return () => h(SvgIcon, { icon: iconString })
}

/**
 * 根据当前路由获取激活的菜单键
 *
 * @param matched 匹配的路由数组
 * @returns 激活的菜单键数组
 */
export function getActiveMenuKeys(matched: RouteLocationMatched[]): string[] {
  if (!matched || matched.length === 0) {
    return []
  }

  let routeName = matched[matched.length - 1]?.name as string

  if (!routeName) {
    return []
  }

  // 如果子路由名称以 _content 结尾，使用父路由名称
  // 这是布局组件的特殊处理：布局组件作为父路由，实际页面作为子路由
  if (routeName.endsWith('_content')) {
    routeName = routeName.replace('_content', '')
  }

  // 如果处理后的路由名称不在 matched 中（可能是去掉了后缀），需要找到对应的路由记录
  // 这确保了菜单 key 与路由 name 的一致性
  const matchedRoute = matched.find((r) => r.name === routeName)
  if (!matchedRoute && routeName.endsWith('_content')) {
    // 如果还是找不到，尝试从原始路由中查找
    routeName = matched[matched.length - 1]?.name as string
  }

  return [routeName]
}

/**
 * 根据当前路由获取打开的菜单键
 *
 * @param matched 匹配的路由数组
 * @returns 打开的菜单键数组
 */
export function getOpenMenuKeys(matched: RouteLocationMatched[]): string[] {
  if (!matched || matched.length === 0) {
    return []
  }

  // 获取除了最后一个之外的所有父级路由
  const parentRoutes = matched.slice(0, -1)
  return parentRoutes.filter((r) => r.name && !r.meta?.hidden).map((r) => r.name as string)
}
