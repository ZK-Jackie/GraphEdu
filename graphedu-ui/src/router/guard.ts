/**
 * 路由守卫
 *
 * 功能：
 * 1. 权限验证 - 检查用户是否已登录
 * 2. 动态路由加载 - 根据路由场景加载对应菜单（web/admin/mobile）
 * 3. 页面标题设置
 */
import picomatch from 'picomatch'
import type { Router, RouteLocationNormalizedGeneric } from 'vue-router'
import type { SceneType } from '@/stores/modules/function'
import useUserStore from '@/stores/modules/user'
import useFunctionStore, { register404Route } from '@/stores/modules/function'

import { getToken } from '@/utils/token.ts'
import { progress } from '@/utils/progress.ts'

/** 白名单路由模式 - 支持通配符，不需要登录即可访问 */
const WHITE_LIST_PATTERNS = ['/login', '/register', '/about', '/privacy', '/terms', '/contact', '/404', '/403', '/']

/**
 * 检查路径是否在白名单中
 * @param path 需要检查的路径
 * @returns 是否在白名单中
 */
function isPathInWhiteList(path: string): boolean {
  return WHITE_LIST_PATTERNS.some((pattern) => {
    const isMatch = picomatch(pattern)
    return isMatch(path)
  })
}

/**
 * 不同场景的动态路由加载状态
 * 注意：这是模块级变量，页面刷新后会重置
 * 因此我们需要额外检查路由是否实际存在
 */
const sceneLoadStates: Record<SceneType, boolean> = {
  web: false,
  admin: false,
  mobile: false,
  userInfo: false,
}

/**
 * 检查场景的路由是否已加载
 * 通过检查该场景的动态路由是否存在来判断
 * @param scene 场景类型
 * @returns 是否已加载
 */
function isSceneRoutesLoaded(scene: SceneType): boolean {
  // 如果状态标记为已加载，直接返回 true
  if (sceneLoadStates[scene]) {
    return true
  }

  // 状态未标记，但可能是页面刷新导致状态丢失
  // 检查 function store 中是否有该场景的菜单数据
  const functionStore = useFunctionStore()

  let loaded = false
  switch (scene) {
    case 'web':
      loaded = functionStore.webLoaded
      break
    case 'admin':
      loaded = functionStore.adminLoaded
      break
    case 'mobile':
      loaded = functionStore.mobileLoaded
      break
    case 'userInfo':
      loaded = functionStore.userInfoLoaded
      break
  }

  // 如果 store 中标记为已加载，同步更新本地状态
  if (loaded) {
    sceneLoadStates[scene] = true
  }

  return loaded
}

/**
 * 根据路由判断场景类型
 * @param route 路由对象
 * @returns 场景类型
 */
function getRouteScene(route: RouteLocationNormalizedGeneric): SceneType | undefined {
  // 优先从路由 meta 中获取场景
  const sceneFromMeta = route.meta?.scene as SceneType | undefined
  if (sceneFromMeta && ['web', 'admin', 'mobile', 'userInfo'].includes(sceneFromMeta)) {
    return sceneFromMeta
  }

  // 根据路径前缀判断场景
  const { path } = route

  // 检查动态路由（通过检查 meta.dynamic 标记）
  if (route.meta?.dynamic) {
    const sceneFromMetaDynamic = route.meta?.scene as SceneType | undefined
    if (sceneFromMetaDynamic && ['web', 'admin', 'mobile', 'userInfo'].includes(sceneFromMetaDynamic)) {
      return sceneFromMetaDynamic
    }
  }

  // 根据路径前缀判断场景（兜底逻辑）
  if (path.startsWith('/admin') || path.startsWith('/system')) {
    return 'admin'
  }
  if (path.startsWith('/mobile')) {
    return 'mobile'
  }
  if (path.startsWith('/profile')) {
    return 'userInfo'
  }

  // 默认为 空
  return undefined
}

/**
 * 设置路由守卫
 * @param router Vue Router 实例
 */
export function setupRouterGuards(router: Router) {
  // 前置守卫
  router.beforeEach(async (to, _from, next) => {
    // 开启进度条
    progress.start()

    const userStore = useUserStore()
    const functionStore = useFunctionStore()

    // 设置页面标题
    document.title = getPageTitle(to.meta.title as string)

    // 检查是否已登录
    if (getToken()) {
      // 已登录
      if (to.path === '/login' || to.path === '/register') {
        // 如果已登录且访问登录页，重定向到首页（使用 replace 避免重复导航）
        next({ path: '/', replace: true })
      } else {
        // 检查是否已加载用户信息
        // 页面刷新后 userId 会丢失，需要重新加载
        const hasUserInfo = !!userStore.userId
        if (!hasUserInfo) {
          // 没有用户信息，需要加载
          try {
            // 加载用户信息
            await userStore.fetchUserInfo()
            // 加载所有场景的菜单数据（预加载）
            await functionStore.loadAllMenuData()
            // 标记所有场景为已加载
            sceneLoadStates.web = true
            sceneLoadStates.admin = true
            sceneLoadStates.mobile = true
            sceneLoadStates.userInfo = true

            // 所有动态路由加载完成后，注册 404 路由
            register404Route()

            // 菜单加载完成后，重新导航到目标路由
            next({ ...to, replace: true })
          } catch (error) {
            console.error('[Router Guard] 加载用户信息或菜单失败:', error)
            // 加载失败，清除 token 并重定向到登录页
            await userStore.logout()
            resetSceneLoadStates()
            next(`/login?redirect=${to.path}`)
          }
        } else {
          // 有用户信息，检查当前场景的菜单是否已加载
          const currentScene = getRouteScene(to)
          // 使用更可靠的检查：通过状态或实际的菜单数据判断
          const isLoaded = currentScene ? isSceneRoutesLoaded(currentScene) : false

          if (!isLoaded && currentScene) {
            // 当前场景的菜单未加载，进行加载
            try {
              const success = await functionStore.loadMenuDataByScene(currentScene)
              if (success) {
                sceneLoadStates[currentScene] = true

                // 检查是否所有场景都已加载，如果是则注册 404 路由
                const allLoaded = Object.values(sceneLoadStates).every((loaded) => loaded)
                if (allLoaded) {
                  register404Route()
                }

                // 菜单加载完成后，重新导航到目标路由
                next({ ...to, replace: true })
              } else {
                console.warn(`[Router Guard] ${currentScene} 场景菜单加载失败`)
                // 加载失败，但不影响访问静态路由
                next()
              }
            } catch (error) {
              console.error(`[Router Guard] 加载 ${currentScene} 场景菜单失败:`, error)
              next()
            }
          } else {
            next()
          }
        }
      }
    } else {
      // 未登录
      if (isPathInWhiteList(to.path)) {
        // 在白名单中，直接放行
        next()
      } else {
        // 不在白名单中，重定向到登录页
        next(`/login?redirect=${to.path}`)
      }
    }
  })

  // 后置守卫
  router.afterEach((_to, _from, failure) => {
    // 关闭进度条
    progress.done()

    // 导航失败处理
    if (failure) {
      console.error('[Router Guard] 导航失败:', failure)
    }
  })

  // 错误处理
  router.onError((_error) => {
    progress.done()
  })
}

/**
 * 重置动态路由加载状态
 * 用于用户登出时重置状态
 */
export function resetDynamicRoutesState() {
  resetSceneLoadStates()
}

/**
 * 重置场景加载状态
 */
export function resetSceneLoadStates() {
  sceneLoadStates.web = false
  sceneLoadStates.admin = false
  sceneLoadStates.mobile = false
  sceneLoadStates.userInfo = false
}

/**
 * 获取页面标题
 * @param pageTitle 页面标题
 * @returns 完整的页面标题
 */
function getPageTitle(pageTitle?: string): string {
  const appName = import.meta.env.VITE_APP_TITLE || 'GraphEdu'

  if (pageTitle) {
    return `${pageTitle} - ${appName}`
  }

  return appName
}

/**
 * 检查路由是否存在
 * @param router Vue Router 实例
 * @param name 路由名称
 * @returns 路由是否存在
 */
export function hasRoute(router: Router, name: string): boolean {
  return router.hasRoute(name)
}

/**
 * 导航到指定路由（带权限检查）
 * @param router Vue Router 实例
 * @param name 路由名称
 * @returns 是否导航成功
 */
export async function navigateTo(router: Router, name: string): Promise<boolean> {
  if (!hasRoute(router, name)) {
    return false
  }
  try {
    await router.push({ name })
    return true
  } catch (_error) {
    return false
  }
}
