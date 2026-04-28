<script setup lang="ts">
import useAppStore from '@/stores/modules/app.ts'
import useUserStore from '@/stores/modules/user.ts'
import { theme } from 'ant-design-vue'

const appStore = useAppStore()
const userStore = useUserStore()
const { darkMode } = storeToRefs(appStore)
const { activeRole } = storeToRefs(userStore)

/**
 * 根据角色 + 亮暗模式动态计算 Ant Design Vue 主题色
 */
const themeConfig = computed(() => {
  const isTeacher = activeRole.value === 'teacher'
  let primary = '#1677ff' // 学生亮色（默认）
  if (isTeacher && darkMode.value) {
    primary = '#34c77e'
  } else if (isTeacher) {
    primary = '#10b981'
  } else if (darkMode.value) {
    primary = '#5598eb'
  }

  return {
    algorithm: darkMode.value ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: primary,
    },
  }
})

/**
 * 同步 data-role 属性到 <html>，驱动 CSS 变量切换
 */
watchEffect(() => {
  const role = activeRole.value
  if (role === 'student' || role === 'teacher') {
    document.documentElement.dataset.role = role
  } else {
    delete document.documentElement.dataset.role
  }
})
</script>

<template>
  <a-config-provider :theme="themeConfig">
    <RouterView class="app" />
  </a-config-provider>
</template>

<style scoped>
@reference "#main.css";

.app {
  @apply bg-[var(--ge-bg-page)];
}
</style>
