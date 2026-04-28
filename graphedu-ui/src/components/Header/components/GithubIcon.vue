<script setup lang="ts">
import { GithubOutlined, ExportOutlined } from '@ant-design/icons-vue'
import { ViteEnv } from '@/constants.ts'

const githubUrl = ViteEnv.VITE_GIT_REMOTE_URL.split('.git')[0]
</script>

<template>
  <a v-if="githubUrl" :href="githubUrl" target="_blank" rel="noopener noreferrer" class="nav-github-btn">
    <a-tooltip placement="bottom" arrow-point-at-center>
      <template #title>
        <span class="flex items-center gap-1">
          访问 GitHub 仓库
          <ExportOutlined class="text-xs" />
        </span>
      </template>
      <GithubOutlined class="nav-github-icon nav-hoverable-item" />
    </a-tooltip>
  </a>
  <span v-else class="nav-github-btn">
    <a-tooltip placement="bottom" arrow-point-at-center>
      <template #title>
        <span>GitHub 仓库未配置</span>
      </template>
      <GithubOutlined class="nav-github-icon text-gray-400" />
    </a-tooltip>
  </span>
</template>

<style scoped>
@reference "#main.css";

.nav-github-btn {
  @apply flex items-center justify-center;
  text-decoration: none;
  background: transparent;
  padding: 0;
  outline: none;
  appearance: none;
}

.nav-github-icon {
  @apply flex items-center justify-center text-3xl text-gray-700 dark:text-gray-300;
  transition: transform 0.2s ease-out;
}

.nav-github-btn:hover .nav-github-icon {
  transform: scale(1.1);
}
</style>
