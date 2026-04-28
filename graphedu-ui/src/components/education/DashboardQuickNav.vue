<script setup lang="ts">
/**
 * DashboardQuickNav - Dashboard 顶部快捷导航栏
 *
 * 显示当前角色标签、角色切换（多角色时）、以及快捷链接
 */
import { BookOutlined, PlusOutlined, SettingOutlined, SwapOutlined } from '@ant-design/icons-vue'
import useUserStore from '@/stores/modules/user'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()

/** 切换到指定角色 */
function switchRole(role: 'student' | 'teacher' | 'admin') {
  userStore.setActiveRole(role)
  router.replace({ path: route.path, query: { ...route.query, role } })
}

/** 快捷链接 */
const quickLinks = computed(() => {
  const links: Array<{ label: string; path: string; icon: any }> = []
  if (userStore.isStudent) {
    links.push({ label: '浏览课程', path: '/learn/course', icon: BookOutlined })
  }
  if (userStore.isTeacher) {
    links.push({ label: '创建课程', path: '/learn/course', icon: PlusOutlined })
  }
  if (userStore.isAdmin) {
    links.push({ label: '管理后台', path: '/admin', icon: SettingOutlined })
  }
  return links
})

/** 角色标签颜色 */
const roleColorMap: Record<string, string> = {
  student: '#667eea',
  teacher: '#10b981',
  admin: '#ef4444',
}
</script>

<template>
  <div v-if="userStore.isLoggedIn" class="quick-nav">
    <!-- 左侧：角色标签 -->
    <div class="nav-left">
      <span
        v-for="role in userStore.availableRoles"
        :key="role.key"
        class="role-tag"
        :class="{ active: userStore.activeRole === role.key }"
        :style="{
          '--tag-color': roleColorMap[role.key] || '#999',
        }"
        @click="switchRole(role.key)"
      >
        {{ role.label }}
      </span>
      <span v-if="userStore.availableRoles.length > 1" class="switch-hint">
        <SwapOutlined style="font-size: 12px; margin-right: 4px" />
        点击切换视角
      </span>
    </div>

    <!-- 右侧：快捷链接 -->
    <div class="nav-right">
      <a-button v-for="link in quickLinks" :key="link.path" type="text" size="small" @click="router.push(link.path)">
        <template #icon><component :is="link.icon" /></template>
        {{ link.label }}
      </a-button>
    </div>
  </div>
</template>

<style scoped>
@reference '#main.css';

.quick-nav {
  @apply flex items-center justify-between px-6 py-2 mb-2 max-w-7xl mx-auto;
}

.nav-left {
  @apply flex items-center gap-2;
}

.role-tag {
  @apply inline-flex items-center px-3 py-1 rounded-full text-xs font-medium cursor-pointer
    border transition-all duration-200;
  color: var(--tag-color);
  background: color-mix(in srgb, var(--tag-color) 8%, transparent);
  border-color: color-mix(in srgb, var(--tag-color) 20%, transparent);
}

.role-tag:hover {
  background: color-mix(in srgb, var(--tag-color) 15%, transparent);
  transform: scale(1.05);
}

.role-tag.active {
  color: #fff;
  background: var(--tag-color);
  border-color: var(--tag-color);
}

.switch-hint {
  @apply text-xs text-gray-400 flex items-center ml-1;
}

.nav-right {
  @apply flex items-center gap-1;
}
</style>
