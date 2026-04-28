<script setup lang="ts">
import GithubIcon from '@/components/Header/components/GithubIcon.vue'
import DarkModeToggle from '@/components/Header/components/DarkModeToggle.vue'
import { useBreakpoints } from '@/composables/useBreakpoints'

const { isMobile } = useBreakpoints()
</script>

<template>
  <!-- 移动端底部工具栏 -->
  <div v-if="isMobile" class="mobile-bottom-bar">
    <!-- GitHub 链接 -->
    <a
      href="https://github.com/yourusername/yourrepo"
      target="_blank"
      rel="noopener noreferrer"
      class="bottom-bar-item"
    >
      <GithubIcon />
      <span>GitHub</span>
    </a>

    <!-- 暗色模式切换 -->
    <button class="bottom-bar-item">
      <DarkModeToggle />
      <span>主题</span>
    </button>
  </div>
</template>

<style scoped>
@reference "#main.css";

.mobile-bottom-bar {
  @apply fixed bottom-0 left-0 right-0 h-16 z-50;
  @apply flex items-center justify-around;
  @apply bg-white dark:bg-gray-800;
  @apply border-t border-gray-200 dark:border-gray-700;
  @apply shadow-lg;
}

.bottom-bar-item {
  @apply flex flex-col items-center justify-center;
  @apply text-gray-700 dark:text-gray-300;
  @apply hover:text-gray-900 dark:hover:text-gray-100;
  @apply transition-colors duration-200;
  @apply cursor-pointer;
  @apply w-full h-full;
  border: none;
  outline: none;
  background: transparent;
  text-decoration: none;
  font-size: 0.75rem;
}

.bottom-bar-item:hover {
  @apply bg-gray-100 dark:bg-gray-700;
}

.bottom-bar-item span {
  @apply mt-1;
}
</style>
