import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { CommonLayout } from '@/layout/index.ts'
import { setupRouterGuards } from './guard'

/**
 * 静态路由配置
 * 这些路由会在应用初始化时直接加载，不依赖后端权限数据
 *
 * 路由元信息字段说明：
 * - title: 页面标题，显示在浏览器标签和面包屑中
 * - icon: 菜单图标
 * - hidden: 是否在菜单中隐藏
 * - keepAlive: 是否缓存页面组件
 * - requiresAuth: 是否需要登录（默认 true）
 * - order: 菜单排序，数字越小越靠前
 * - affix: 是否固定在标签页（不可关闭）
 * - scene: 应用场景（'web'-日常应用, 'admin'-管理系统, 'mobile'-移动端）
 *
 * 注意：
 * - web 场景的公开页面放在这里
 * - admin 场景的路由完全从后端动态获取
 */
export const constantRoutes: RouteRecordRaw[] = [
  // 404 页面通配符路由已移除，改为动态注册
  // 具体实现：在所有动态路由加载完成后，通过 register404Route() 函数动态添加
  // 这样可以确保动态路由优先匹配，避免 404 路由过早拦截

  // 公开页面（统一使用 CommonLayout）
  {
    path: '/',
    component: CommonLayout,
    meta: { requiresAuth: false },
    children: [
      {
        path: '',
        name: 'indexHome',
        alias: ['/index', '/home'],
        component: () => import('@/views/index.vue'),
        meta: {
          title: '首页',
          icon: 'home',
          hidden: true,
          order: 0,
          scene: 'web',
        },
      },
      {
        path: 'login',
        name: 'login',
        component: () => import('@/views/LoginView.vue'),
        meta: {
          title: '登录',
          hidden: true,
          requiresAuth: false,
        },
      },
      {
        path: 'register',
        name: 'register',
        component: () => import('@/views/RegisterView.vue'),
        meta: {
          title: '注册',
          hidden: true,
          requiresAuth: false,
        },
      },
      {
        path: 'about',
        name: 'about',
        component: () => import('@/views/AboutView.vue'),
        meta: {
          title: '关于我们',
          hidden: true,
          requiresAuth: false,
        },
      },
      {
        path: 'privacy',
        name: 'privacy',
        component: () => import('@/views/PrivacyView.vue'),
        meta: {
          title: '隐私政策',
          hidden: true,
          requiresAuth: false,
        },
      },
      {
        path: 'terms',
        name: 'terms',
        component: () => import('@/views/TermsView.vue'),
        meta: {
          title: '使用条款',
          hidden: true,
          requiresAuth: false,
        },
      },
      {
        path: 'contact',
        name: 'contact',
        component: () => import('@/views/ContactView.vue'),
        meta: {
          title: '联系我们',
          hidden: true,
          requiresAuth: false,
        },
      },
    ],
  },
]

/**
 * 创建 Vue Router 实例
 */
const router = createRouter({
  history: createWebHistory(import.meta.env.VITE_APP_BASE_URL),
  routes: constantRoutes,
  // 路由跳转后滚动到顶部
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0 }
  },
})

// 设置路由守卫
setupRouterGuards(router)

export default router
