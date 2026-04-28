<script setup lang="ts">
/**
 * RoleSwitcher - 角色视角切换器
 *
 * 当用户同时拥有学生和教师身份时，在 Header 右上角显示切换按钮。
 * 切换后通过 URL param ?role=xxx 同步状态，刷新后仍可恢复。
 */
import { SwapOutlined } from '@ant-design/icons-vue'
import useUserStore from '@/stores/modules/user'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()

/** 切换角色视角 */
function handleSwitchRole() {
  const target = userStore.activeRole === 'student' ? 'teacher' : 'student'
  userStore.setActiveRole(target)
  // 通过 URL param 持久化角色选择
  router.replace({ path: route.path, query: { ...route.query, role: target } })
}
</script>

<template>
  <a-tooltip v-if="userStore.hasMultipleRoles" title="切换角色视角">
    <button class="role-switcher" @click="handleSwitchRole">
      <SwapOutlined class="role-switcher-icon" />
      <span class="role-switcher-label">{{ userStore.activeRoleLabel }}</span>
    </button>
  </a-tooltip>
</template>

<style scoped>
@reference '#main.css';

.role-switcher {
  @apply flex items-center gap-1.5 px-2.5 h-8 rounded-full text-xs font-medium
    cursor-pointer border-none transition-all duration-200 ease-out;
  background: linear-gradient(135deg, #667eea15, #764ba215);
  color: #667eea;
}

.role-switcher:hover {
  background: linear-gradient(135deg, #667eea25, #764ba225);
  transform: scale(1.05);
}

.role-switcher-icon {
  @apply text-sm;
}

.role-switcher-label {
  @apply text-xs;
}
</style>
