<script setup lang="ts">
/**
 * CommonLayout - 通用布局
 *
 * 结构：
 * - 顶部：固定导航栏（CommonHeader）
 * - 中间：路由页面内容区域
 * - 底部：Footer（CommonFooter）
 *
 * 适用场景：首页、登录、注册、关于页、文档页等不需要侧边栏和复杂布局的页面
 */
import { CommonFooter } from './components'
import MobileDrawer from './components/MobileDrawer.vue'
import Header from '@/components/Header/index.vue'
import useUserStore from '@/stores/modules/user'
import useFunctionStore from '@/stores/modules/function'

const route = useRoute()
const userStore = useUserStore()
const functionStore = useFunctionStore()

const { token } = storeToRefs(userStore)

/** 是否已登录 */
const isLoggedIn = computed(() => !!token?.value)

/** 是否有 web 场景菜单项 */
const hasWebMenu = computed(() => functionStore.webMenuItems.length > 0)

/** 是否显示顶部导航菜单（登录态且有菜单数据时才显示） */
const showMenu = computed(() => isLoggedIn.value && hasWebMenu.value)

type DisplayItem = 'github' | 'darkMode' | 'userAvatar' | 'loginBtn' | 'registerBtn'

/** 根据认证状态和当前路由动态计算右侧按钮 */
const headerDisplayItems = computed<DisplayItem[]>(() => {
  if (isLoggedIn.value) {
    return ['github', 'darkMode', 'userAvatar']
  }
  const path = route.path
  if (path === '/login') {
    return ['github', 'darkMode', 'registerBtn']
  }
  if (path === '/register') {
    return ['github', 'darkMode', 'loginBtn']
  }
  return ['github', 'darkMode', 'userAvatar']
})
</script>

<template>
  <div class="common-layout">
    <!-- 顶部导航栏 -->
    <Header class="common-layout-header" :show-menu="showMenu" :display-items="headerDisplayItems" />

    <!-- 移动端导航抽屉 -->
    <MobileDrawer />

    <!-- 主内容区域 -->
    <main class="common-layout-main">
      <router-view v-slot="{ Component, route }">
        <transition name="fade" mode="out-in" :duration="200">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </main>

    <!-- 底部信息栏 -->
    <CommonFooter />
  </div>
</template>

<style scoped>
@reference "#main.css";

.common-layout {
  @apply min-h-screen w-full flex flex-col;
  background: var(--ge-bg-page);
}

.common-layout-header {
  @apply top-0 left-0 w-full z-50 h-20;
  /* 固定高度，防止压缩 */
  flex-shrink: 0;
}

.common-layout-main {
  /* 占满父 flex 剩余空间，作为 flex 列容器向下传递高度 */
  @apply flex-1 mt-1 w-full flex flex-col overflow-hidden;

  /* 防止 flex 子元素溢出撑开父容器 */
  min-height: 0;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
