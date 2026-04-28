<script setup lang="ts">
/**
 * CommonHeader - 通用布局的头部导航栏
 *
 * 桌面端：
 * - 左侧：Logo + 文字（点击进入首页） + 导航项
 * - 右侧：GitHub 图标 + 深色模式切换 + 用户头像
 *
 * 移动端：
 * - 左侧：汉堡图标（点击触发抽屉）
 * - 右侧：用户头像
 * - Logo、导航项、GitHub、暗色模式移入抽屉
 */
import { Divider } from 'ant-design-vue'
import type { MenuProps } from 'ant-design-vue'
import { MenuOutlined } from '@ant-design/icons-vue'
import GithubIcon from '@/components/Header/components/GithubIcon.vue'
import DarkModeToggle from '@/components/Header/components/DarkModeToggle.vue'
import UserAvatar from '@/components/Header/components/UserAvatar.vue'
import Logo from '@/components/Header/components/Logo.vue'
import useAppStore from '@/stores/modules/app.ts'
import useFunctionStore from '@/stores/modules/function.ts'
import { getActiveMenuKeys } from '@/router/utils.ts'
import LoginRegister from '@/components/Header/components/LoginRegister.vue'
import { useBreakpoints } from '@/composables/useBreakpoints.ts'

interface HeaderProps {
  showMenu?: boolean
  displayItems?: ('github' | 'darkMode' | 'userAvatar' | 'loginBtn' | 'registerBtn')[]
}

const props = withDefaults(defineProps<HeaderProps>(), {
  showMenu: true,
  displayItems: () => ['github', 'darkMode', 'userAvatar'],
})

const itemsMapping: Record<string, any> = {
  github: GithubIcon,
  darkMode: DarkModeToggle,
  userAvatar: UserAvatar,
  loginRegister: LoginRegister,
}

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const functionStore = useFunctionStore()
const { darkMode } = storeToRefs(appStore)
const { isMobile, isTablet } = useBreakpoints()

// 当前选中的菜单项
const selectedKeys = ref<string[]>([])

/**
 * 获取菜单项
 * 从 function store 获取 web 场景的顶部菜单配置
 */
const menuItems = computed(() => functionStore.webMenuItems)

/**
 * 获取右侧工具按钮组件列表
 * 移动端和桌面端统一逻辑，所有 displayItems 都在右侧显示
 */
const navRightComponents: ComputedRef<any[]> = computed(() => {
  const ret: any[] = []
  props.displayItems.forEach((item) => {
    let component: any = null
    const itemProps: any = { class: 'nav-item' }

    if (item === 'loginBtn') {
      component = LoginRegister
      itemProps.status = 'login'
    } else if (item === 'registerBtn') {
      component = LoginRegister
      itemProps.status = 'register'
    } else if (itemsMapping[item]) {
      component = itemsMapping[item]
    }

    if (component) {
      ret.push({ component, props: itemProps })
      ret.push({
        component: Divider,
        props: { type: 'vertical', class: 'nav-divider' },
      })
    }
  })
  // 移除最后一个分割线
  if (ret.length > 0 && ret[ret.length - 1].component === Divider) {
    ret.pop()
  }
  return ret
})

/**
 * 根据当前路由更新选中的菜单项
 */
watch(
  () => route.matched,
  (matched) => {
    selectedKeys.value = getActiveMenuKeys(matched)
  },
  { immediate: true }
)

/**
 * 菜单点击事件
 */
const handleMenuClick: MenuProps['onClick'] = ({ item }) => {
  router.push({ path: item.path as string })
}

/** 是否显示汉堡菜单触发器：有菜单数据时，移动端始终显示；平板端仅在没有水平菜单时显示 */
const showMobileTrigger = computed(() => {
  if (!menuItems.value.length) return false
  return isMobile.value || (isTablet.value && !props.showMenu)
})

/** 移动端：点击汉堡图标打开抽屉 */
const handleMobileTrigger = () => {
  appStore.toggleMobileMenuDrawer()
}
</script>

<template>
  <nav class="header-nav">
    <!-- 左侧 -->
    <div class="nav-left">
      <!-- 移动端/平板端无菜单时：汉堡图标（触发抽屉） -->
      <button v-if="showMobileTrigger" class="mobile-trigger" @click="handleMobileTrigger">
        <MenuOutlined class="mobile-trigger-icon" />
      </button>

      <!-- 桌面端：Logo 和标题 -->
      <Logo v-if="!showMobileTrigger" class="nav-left-logo" />

      <!-- 桌面端：导航菜单 -->
      <a-menu
        v-if="showMenu && !isMobile"
        v-model:selected-keys="selectedKeys"
        :theme="darkMode ? 'dark' : 'light'"
        mode="horizontal"
        class="header-menu"
        :items="menuItems"
        @click="handleMenuClick"
      />
    </div>

    <!-- 右侧：工具按钮 -->
    <div class="nav-right">
      <component v-bind="item.props" :is="item.component" v-for="(item, index) in navRightComponents" :key="index" />
    </div>
  </nav>
</template>

<style scoped>
@reference "#main.css";

.header-nav {
  @apply shadow-md pt-2 pb-1 px-5 flex justify-between items-center;
  background: var(--ge-bg-container);
}

/* 左侧区域 */
.nav-left {
  @apply flex items-center gap-8 h-full;
}

/* 顶部菜单 */
.header-menu {
  @apply border-b-0;
}

/* 右侧区域 */
.nav-right {
  @apply flex items-center h-full;
}

/* 移动端汉堡图标 */
.mobile-trigger {
  @apply p-0 border-none bg-transparent cursor-pointer flex items-center justify-center;
  @apply text-xl text-gray-700 dark:text-gray-300;
  transition: color 0.2s;
}

.mobile-trigger:hover {
  @apply text-blue-600 dark:text-blue-400;
}

.mobile-trigger-icon {
  @apply text-xl;
}

.nav-item {
  @apply px-2 h-10 rounded-md
  cursor-pointer
  flex items-center justify-center
  border-none bg-transparent
  transition-all duration-200 ease-out;
}

.nav-item:hover {
  background: var(--ge-bg-elevated);
}

.nav-divider {
  @apply h-6;
  background: var(--ge-border-color);
}
</style>
