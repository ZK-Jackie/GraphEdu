<script setup lang="ts">
import { UserOutlined, HolderOutlined } from '@ant-design/icons-vue'
import type { MenuProps } from 'ant-design-vue'
import type { SubMenuType, MenuItemType } from 'ant-design-vue/es/menu/src/hooks/useItems'
import useUserStore from '@/stores/modules/user.ts'
import useFunctionStore from '@/stores/modules/function.ts'

/** 可渲染的菜单项（含 label/key/icon，可能带 children） */
type RenderableMenuItem = (MenuItemType | SubMenuType) & {
  label?: string
  icon?: any
}

const userStore = useUserStore()
const functionStore = useFunctionStore()
const router = useRouter()
const route = useRoute()

const { avatar, token } = storeToRefs(userStore)
const isLogin = computed(() => !!token?.value)

/**
 * 将 ItemType 转为可安全渲染的菜单项数组。
 * 过滤掉 null、divider、group 等不具备 label/key 的类型。
 */
const renderableMenuItems = computed<RenderableMenuItem[]>(() =>
  (functionStore.userInfoMenuItems ?? []).filter(
    (item): item is RenderableMenuItem => item != null && 'label' in item && 'key' in item
  )
)

// 处理菜单点击事件
const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
  if (key === route.name) {
    return
  }
  if (key === 'logout') {
    handleLogout()
  } else {
    // 处理其他菜单项的点击事件，例如跳转到个人中心等
    router.push({ name: key as string })
  }
}

// 处理退出登录
const handleLogout = async () => {
  await userStore.logout()
  router.push('/login')
}
</script>

<template>
  <a-dropdown v-if="isLogin" :trigger="['click', 'hover']" placement="bottomRight">
    <div class="user-center user-center-trigger">
      <img :src="avatar" alt="avatar" class="nav-user-icon" />
      <HolderOutlined class="nav-user-icon-bar" />
    </div>
    <template #overlay>
      <a-menu @click="handleMenuClick">
        <!-- 渲染 userInfo 场景的菜单 -->
        <template v-for="item in renderableMenuItems" :key="item.key">
          <a-menu-item v-if="!('children' in item) || !item.children?.length" :key="String(item.key)">
            <template v-if="item.icon" #icon>
              <component :is="item.icon" />
            </template>
            {{ item.label }}
          </a-menu-item>
          <!-- 如果有子菜单，使用子菜单 -->
          <a-sub-menu v-else :key="String(item.key)">
            <template v-if="item.icon" #icon>
              <component :is="item.icon" />
            </template>
            <template #title>{{ item.label }}</template>
            <a-menu-item v-for="child in (item as SubMenuType).children?.filter?.((c): c is MenuItemType => c != null && 'key' in c) ?? []" :key="String(child.key)">
              <template v-if="('icon' in child) && child.icon" #icon>
                <component :is="(child as any).icon" />
              </template>
              {{ ('label' in child) ? child.label : '' }}
            </a-menu-item>
          </a-sub-menu>
        </template>
        <a-menu-divider />
        <a-menu-item key="logout" @click="handleLogout">
          <template #icon>
            <UserOutlined />
          </template>
          退出登录
        </a-menu-item>
      </a-menu>
    </template>
  </a-dropdown>
  <a v-else class="user-center-trigger" href="/login">
    <a-tooltip>
      <template #title>
        <span>登录 / 注册</span>
      </template>
      <UserOutlined class="nav-login-register-icon" />
    </a-tooltip>
  </a>
</template>

<style scoped>
@reference "#main.css";

.nav-user-icon {
  @apply h-8 w-8 object-cover rounded-full;
  transition: transform 0.2s ease-out;
}

.nav-login-register-icon {
  @apply text-2xl;
}

.user-center {
  @apply flex items-center justify-center gap-1 cursor-pointer;
}

.user-center-trigger {
  @apply text-xl text-gray-700 dark:text-gray-300;
  transition: transform 0.2s ease-out;
}

/* 当悬浮在整个 nav-user-center 区域时，触发图标缩放效果 */
.user-center:hover .nav-user-icon,
.user-center:hover .user-center-trigger {
  transform: scale(1.1);
}

.user-center:hover .nav-user-icon-bar {
  transition: transform 0.3s ease-out;
  transform: scale(1.2);
}
</style>
