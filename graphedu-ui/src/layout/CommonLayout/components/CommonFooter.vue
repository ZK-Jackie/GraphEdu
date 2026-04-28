<script setup lang="ts">
/**
 * CommonFooter - 通用布局的底部信息栏
 *
 * 显示版权信息、备案信息、版本信息、链接等
 */
import { ViteEnv } from '@/constants.ts'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const currentYear = new Date().getFullYear()

// 备案信息
const icpLicense = ViteEnv.VITE_ICP_LICENSE
const psaLicense = ViteEnv.VITE_PSA_LICENSE

// 版本信息：优先显示 TAG，否则显示 commit hash
const versionInfo = computed(() => {
  const tag = ViteEnv.VITE_GIT_TAG
  const hash = ViteEnv.VITE_GIT_COMMIT_HASH
  return tag || hash || ''
})

// 是否有额外信息（备案或版本）
const hasExtraInfo = computed(() => {
  return !!(icpLicense || psaLicense || versionInfo.value)
})

// 底部链接配置
const footerLinks = ref([
  { label: '关于我们', path: '/about' },
  { label: '隐私政策', path: '/privacy' },
  { label: '使用条款', path: '/terms' },
  { label: '联系我们', path: '/contact' },
])
</script>

<template>
  <footer class="common-footer">
    <div class="footer-content">
      <!-- 主要内容区域 -->
      <div class="footer-main">
        <!-- 版权信息 -->
        <div class="footer-copyright">
          <p class="copyright-text">© {{ currentYear }} {{ t('header.nav.title') }}. All rights reserved.</p>
        </div>

        <!-- 备案信息和版本信息 -->
        <div v-if="hasExtraInfo" class="footer-meta">
          <!-- ICP 备案 -->
          <a
            v-if="icpLicense"
            href="https://beian.miit.gov.cn/"
            target="_blank"
            rel="noopener noreferrer"
            class="footer-meta-item"
          >
            {{ icpLicense }}
          </a>

          <!-- 公安备案 -->
          <a
            v-if="psaLicense"
            :href="`http://www.beian.gov.cn/portal/registerSystemInfo?recordcode=${psaLicense.match(/\d+/)?.[0] || ''}`"
            target="_blank"
            rel="noopener noreferrer"
            class="footer-meta-item psa-license"
          >
            <img src="https://beian.mps.gov.cn/img/logo01.dd7ff50e.png" alt="公安" class="psa-icon" />
            {{ psaLicense }}
          </a>

          <!-- 版本信息 -->
          <a
            v-if="versionInfo"
            :href="`${ViteEnv.VITE_GIT_REMOTE_URL || ''}/releases`"
            target="_blank"
            rel="noopener noreferrer"
            class="footer-meta-item version-info"
          >
            {{ versionInfo }}
          </a>
        </div>
      </div>

      <!-- 底部链接 -->
      <div class="footer-links">
        <router-link v-for="link in footerLinks" :key="link.path" :to="link.path" class="footer-link">
          {{ link.label }}
        </router-link>
      </div>
    </div>
  </footer>
</template>

<style scoped>
@reference '#main.css';

.common-footer {
  @apply w-full bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 py-6 px-6;
}

.footer-content {
  @apply max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4;
}

.footer-main {
  @apply flex flex-col items-center md:items-start gap-2;
}

.footer-copyright {
  @apply text-gray-600 dark:text-gray-400;
}

.copyright-text {
  @apply text-sm mb-0;
}

.footer-meta {
  @apply flex flex-wrap items-center justify-center md:justify-start gap-3;
}

.footer-meta-item {
  @apply text-xs text-gray-500 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 transition-colors no-underline flex items-center;
}

.psa-license {
  @apply flex items-center gap-1;
}

.psa-icon {
  @apply w-3 h-3 object-contain;
}

.version-info {
  @apply font-mono;
}

.footer-links {
  @apply flex flex-wrap items-center justify-center gap-6;
}

.footer-link {
  @apply text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors no-underline select-none;
}
</style>
