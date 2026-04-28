import type { FunctionTreeVO } from '@/types/api/system/function.ts'
import type { ItemType } from 'ant-design-vue'
import type { RouteRecordRaw } from 'vue-router'
import { getMenus } from '@/api/system/auth'
import { transformFunctionToMenu, transformFunctionToRoute } from '@/router/utils'
import router, { constantRoutes } from '@/router'

/** 场景类型 */
export type SceneType = 'web' | 'admin' | 'mobile' | 'userInfo'

interface FunctionState {
  /** 日常应用菜单树（顶部导航） */
  webMenuTree: FunctionTreeVO[]
  /** 管理系统菜单树（侧边栏） */
  adminMenuTree: FunctionTreeVO[]
  /** 移动端菜单树 */
  mobileMenuTree: FunctionTreeVO[]
  /** 个人中心菜单树 */
  userInfoMenuTree: FunctionTreeVO[]
  /** web 场景是否已加载 */
  webLoaded: boolean
  /** admin 场景是否已加载 */
  adminLoaded: boolean
  /** mobile 场景是否已加载 */
  mobileLoaded: boolean
  /** userInfo 场景是否已加载 */
  userInfoLoaded: boolean
  /** 动态路由列表（已注册的） */
  dynamicRoutes: RouteRecordRaw[]
}

const useFunctionStore = defineStore('function', {
  state: (): FunctionState => ({
    webMenuTree: [],
    adminMenuTree: [],
    mobileMenuTree: [],
    userInfoMenuTree: [],
    webLoaded: false,
    adminLoaded: false,
    mobileLoaded: false,
    userInfoLoaded: false,
    dynamicRoutes: [],
  }),

  getters: {
    /**
     * 获取日常应用菜单项（顶部导航）
     * Ant Design Menu 格式
     */
    webMenuItems(state): ItemType[] {
      if (!state.webMenuTree.length) {
        return []
      }
      return transformFunctionToMenu(state.webMenuTree)
    },

    /**
     * 获取管理系统菜单项（侧边栏）
     * Ant Design Menu 格式
     */
    adminMenuItems(state): ItemType[] {
      if (!state.adminMenuTree.length) {
        return []
      }
      return transformFunctionToMenu(state.adminMenuTree)
    },

    /**
     * 获取移动端菜单项
     * Ant Design Menu 格式
     */
    mobileMenuItems(state): ItemType[] {
      if (!state.mobileMenuTree.length) {
        return []
      }
      return transformFunctionToMenu(state.mobileMenuTree)
    },

    /**
     * 获取个人中心菜单项
     * Ant Design Menu 格式
     */
    userInfoMenuItems(state): ItemType[] {
      if (!state.userInfoMenuTree.length) {
        return []
      }
      return transformFunctionToMenu(state.userInfoMenuTree)
    },

    /**
     * 根据 scene 获取对应的菜单数据
     */
    getMenuByScene:
      (state) =>
      (scene: SceneType): FunctionTreeVO[] => {
        switch (scene) {
          case 'web':
            return state.webMenuTree
          case 'admin':
            return state.adminMenuTree
          case 'mobile':
            return state.mobileMenuTree
          case 'userInfo':
            return state.userInfoMenuTree
          default:
            return []
        }
      },

    /**
     * 根据 scene 获取对应的菜单项
     */
    getMenuItemsByScene:
      (state) =>
      (scene: SceneType): ItemType[] => {
        switch (scene) {
          case 'web':
            return transformFunctionToMenu(state.webMenuTree)
          case 'admin':
            return transformFunctionToMenu(state.adminMenuTree)
          case 'mobile':
            return transformFunctionToMenu(state.mobileMenuTree)
          case 'userInfo':
            return transformFunctionToMenu(state.userInfoMenuTree)
          default:
            return []
        }
      },

    /**
     * 检查指定场景是否已加载
     */
    isSceneLoaded:
      (state) =>
      (scene: SceneType): boolean => {
        switch (scene) {
          case 'web':
            return state.webLoaded
          case 'admin':
            return state.adminLoaded
          case 'mobile':
            return state.mobileLoaded
          case 'userInfo':
            return state.userInfoLoaded
          default:
            return false
        }
      },

    /**
     * 所有路由列表（静态 + 动态）
     */
    allRoutes(state): RouteRecordRaw[] {
      return [...constantRoutes, ...state.dynamicRoutes]
    },
  },

  actions: {
    /**
     * 加载指定场景的菜单数据
     * @param scene 应用场景
     * @returns 是否加载成功
     */
    async loadMenuDataByScene(scene: SceneType): Promise<boolean> {
      try {
        console.log(`[Function Store] 开始加载 ${scene} 场景菜单数据...`)

        const response = await getMenus(scene)
        const menuTree = response.data || []

        // 根据场景存储到对应的状态
        switch (scene) {
          case 'web':
            this.webMenuTree = menuTree
            this.webLoaded = true
            // web 场景也需要注册动态路由
            await this.registerRoutesByScene('web', menuTree)
            break
          case 'admin':
            this.adminMenuTree = menuTree
            this.adminLoaded = true
            // admin 场景需要注册动态路由
            await this.registerRoutesByScene('admin', menuTree)
            break
          case 'mobile':
            this.mobileMenuTree = menuTree
            this.mobileLoaded = true
            // mobile 场景也需要注册动态路由
            await this.registerRoutesByScene('mobile', menuTree)
            break
          case 'userInfo':
            this.userInfoMenuTree = menuTree
            this.userInfoLoaded = true
            // userInfo 场景也需要注册动态路由
            await this.registerRoutesByScene('userInfo', menuTree)
            break
        }
        return true
      } catch (error) {
        console.error(`[Function Store] 加载 ${scene} 场景菜单数据失败:`, error)
        return false
      }
    },

    /**
     * 加载所有场景的菜单数据（用于登录后预加载）
     */
    async loadAllMenuData(): Promise<void> {
      // 并行加载所有场景的菜单（内部不再各自处理 404 路由）
      await Promise.allSettled([
        this.loadMenuDataByScene('web'),
        this.loadMenuDataByScene('admin'),
        this.loadMenuDataByScene('userInfo'),
      ])
    },

    /**
     * 根据场景注册动态路由到 Vue Router
     * @param scene 应用场景
     * @param menuTree 菜单树数据
     */
    async registerRoutesByScene(scene: SceneType, menuTree: FunctionTreeVO[]): Promise<void> {
      if (!menuTree.length) {
        return
      }

      try {
        // 转换为路由配置
        const routes = transformFunctionToRoute(menuTree)

        if (routes.length === 0) {
          return
        }
        // 注册新路由（不清除其他场景的路由）
        for (const route of routes) {
          try {
            // 检测路由冲突（静默检测，开发环境下打印）
            if (route.name && router.hasRoute(route.name as string)) {
              continue
            }
            router.addRoute(route)
            this.dynamicRoutes.push(route)
          } catch (error) {
            const routeName = route.name ? String(route.name) : 'unknown'
            console.error(`[Function Store] 注册${scene}场景路由失败: ${routeName}`, error)
          }
        }
      } catch (error) {
        console.error(`[Function Store] 注册${scene}场景动态路由失败:`, error)
        throw error
      }
    },

    /**
     * 打印路由树结构（只打印顶级动态路由）
     * @param routes 路由列表
     */
    printRouteTree(routes: any[]): void {
      // 只打印没有父路由的路由（顶级路由）
      const topRoutes = routes.filter((r) => {
        // 检查是否有父路由（通过匹配记录）
        const hasParent = r.matched && r.matched.length > 1
        return !hasParent && r.meta?.dynamic
      })

      for (const route of topRoutes) {
        console.log(`[Route] ${route.path} (${route.name})`)
        if (route.children && route.children.length > 0) {
          for (const child of route.children) {
            console.log(`[Route]   └─ ${child.path} (${child.name})`)
            if (child.children && child.children.length > 0) {
              for (const grandChild of child.children) {
                console.log(`[Route]     └─ ${grandChild.path} (${grandChild.name})`)
              }
            }
          }
        }
      }
    },

    /**
     * 清除动态路由
     */
    clearDynamicRoutes(): void {
      // 从 router 中移除动态路由
      this.dynamicRoutes.forEach((route) => {
        if (route.name && router.hasRoute(route.name as string)) {
          router.removeRoute(route.name as string)
        }
      })

      this.dynamicRoutes = []
      console.log('[Function Store] 动态路由已清除')
    },

    /**
     * 清空所有菜单数据（用于登出）
     */
    clearMenuData(): void {
      this.clearDynamicRoutes()
      this.webMenuTree = []
      this.adminMenuTree = []
      this.mobileMenuTree = []
      this.userInfoMenuTree = []
      this.webLoaded = false
      this.adminLoaded = false
      this.mobileLoaded = false
      this.userInfoLoaded = false
      console.log('[Function Store] 所有菜单数据已清空')
    },

    /**
     * 清空指定场景的菜单数据
     */
    clearMenuDataByScene(scene: SceneType): void {
      // 清除指定场景的路由
      this.clearRoutesByScene(scene)

      // 清除指定场景的菜单数据
      switch (scene) {
        case 'web':
          this.webMenuTree = []
          this.webLoaded = false
          break
        case 'admin':
          this.adminMenuTree = []
          this.adminLoaded = false
          break
        case 'mobile':
          this.mobileMenuTree = []
          this.mobileLoaded = false
          break
        case 'userInfo':
          this.userInfoMenuTree = []
          this.userInfoLoaded = false
          break
      }
      console.log(`[Function Store] ${scene} 场景菜单数据已清空`)
    },

    /**
     * 清除指定场景的动态路由
     * @param scene 应用场景
     */
    clearRoutesByScene(scene: SceneType): void {
      // 从 dynamicRoutes 中过滤出要删除的路由
      const routesToRemove = this.dynamicRoutes.filter((route) => route.meta?.scene === scene)

      // 从 router 中移除这些路由
      routesToRemove.forEach((route) => {
        if (route.name && router.hasRoute(route.name as string)) {
          router.removeRoute(route.name as string)
        }
      })

      // 从 dynamicRoutes 中移除这些路由
      this.dynamicRoutes = this.dynamicRoutes.filter((route) => route.meta?.scene !== scene)

      console.log(`[Function Store] ${scene} 场景的 ${routesToRemove.length} 个动态路由已清除`)
    },

    /**
     * 刷新指定场景的菜单数据
     */
    async refreshMenuDataByScene(scene: SceneType): Promise<boolean> {
      console.log(`[Function Store] 刷新 ${scene} 场景菜单数据...`)
      this.clearMenuDataByScene(scene)
      return await this.loadMenuDataByScene(scene)
    },

    /**
     * 刷新所有菜单数据
     */
    async refreshAllMenuData(): Promise<void> {
      console.log('[Function Store] 刷新所有场景菜单数据...')
      this.clearMenuData()
      await this.loadAllMenuData()
    },

    /**
     * 检查是否有指定权限（在所有场景的菜单中查找）
     * @param key 权限标识
     */
    hasPermission(key: string): boolean {
      const allMenus = [...this.webMenuTree, ...this.adminMenuTree, ...this.mobileMenuTree, ...this.userInfoMenuTree]

      if (!allMenus.length) {
        return false
      }

      const checkNode = (nodes: FunctionTreeVO[]): boolean => {
        for (const node of nodes) {
          if (node.functionKey === key) {
            return true
          }
          if (node.children && checkNode(node.children)) {
            return true
          }
        }
        return false
      }

      return checkNode(allMenus)
    },

    /**
     * 检查指定场景是否有指定权限
     * @param key 权限标识
     * @param scene 应用场景
     */
    hasPermissionInScene(key: string, scene: SceneType): boolean {
      const menuTree = this.getMenuByScene(scene)

      if (!menuTree.length) {
        return false
      }

      const checkNode = (nodes: FunctionTreeVO[]): boolean => {
        for (const node of nodes) {
          if (node.functionKey === key) {
            return true
          }
          if (node.children && checkNode(node.children)) {
            return true
          }
        }
        return false
      }

      return checkNode(menuTree)
    },
  },
})

export default useFunctionStore

/**
 * 从 function store 同步场景加载状态到路由守卫
 * 用于页面刷新后恢复状态
 */
export function syncSceneLoadStates() {
  const store = useFunctionStore()
  return {
    web: store.webLoaded,
    admin: store.adminLoaded,
    mobile: store.mobileLoaded,
    userInfo: store.userInfoLoaded,
  }
}

/** 404 路由是否已注册 */
let notFoundRouteRegistered = false

/**
 * 注册 404 路由（作为兜底路由）
 * 必须在所有动态路由加载完成后调用
 */
export function register404Route() {
  if (notFoundRouteRegistered) {
    console.log('[Function Store] 404 路由已注册，跳过')
    return
  }

  const notFoundRoute: RouteRecordRaw = {
    path: '/:pathMatch(.*)*',
    name: 'notFound',
    component: () => import('@/views/error/404.vue'),
    meta: {
      title: '页面不存在',
      hidden: true,
      requiresAuth: false,
    },
  }

  router.addRoute(notFoundRoute)
  notFoundRouteRegistered = true
  console.log('[Function Store] 404 路由已注册')
}

/**
 * 移除 404 路由
 * 用于重新加载动态路由时
 */
export function remove404Route() {
  if (notFoundRouteRegistered && router.hasRoute('notFound')) {
    router.removeRoute('notFound')
    notFoundRouteRegistered = false
    console.log('[Function Store] 404 路由已移除')
  }
}
