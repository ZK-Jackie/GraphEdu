<script setup lang="ts">
/**
 * 联系我们页面
 */
import { GithubOutlined, MailOutlined } from '@ant-design/icons-vue'
import CommonPageLayout from '@/layout/CommonPageLayout.vue'

const contactItems = [
  {
    icon: GithubOutlined,
    title: 'GitHub',
    description: '查看项目源码、提交 Issue 或参与贡献',
    link: import.meta.env.VITE_GIT_REMOTE_URL || '',
    linkText: '访问仓库',
  },
  {
    icon: MailOutlined,
    title: '邮件联系',
    description: '如有问题或建议，欢迎通过邮件联系',
    link: '',
    linkText: '',
  },
]
</script>

<template>
  <CommonPageLayout title="联系我们">
    <div class="contact-page">
      <p class="contact-desc">智图学堂是一个毕业设计项目，如果您有任何问题或建议，欢迎通过以下方式联系。</p>

      <div class="contact-list">
        <div v-for="item in contactItems" :key="item.title" class="contact-card">
          <div class="contact-icon">
            <component :is="item.icon" />
          </div>
          <div class="contact-info">
            <h3 class="contact-title">{{ item.title }}</h3>
            <p class="contact-desc-item">{{ item.description }}</p>
            <a v-if="item.link" :href="item.link" target="_blank" rel="noopener noreferrer" class="contact-link">
              {{ item.linkText }}
            </a>
          </div>
        </div>
      </div>
    </div>
  </CommonPageLayout>
</template>

<style scoped>
@reference '#main.css';

.contact-page {
  @apply max-w-2xl mx-auto;
}

.contact-desc {
  @apply mb-8 text-sm leading-relaxed;
  color: var(--ge-text-secondary);
}

.contact-list {
  @apply flex flex-col gap-4;
}

.contact-card {
  @apply flex gap-4 p-5 rounded-lg;
  background: var(--ge-bg-container);
  border: 1px solid var(--ge-border-color);
}

.contact-icon {
  @apply flex items-center justify-center w-10 h-10 rounded-lg shrink-0 text-lg;
  color: var(--ge-primary);
  background: var(--ge-primary-light);
}

.contact-info {
  @apply flex-1;
}

.contact-title {
  @apply text-base font-semibold m-0 mb-1;
  color: var(--ge-text-primary);
}

.contact-desc-item {
  @apply text-sm m-0 mb-2;
  color: var(--ge-text-secondary);
}

.contact-link {
  @apply text-sm;
  color: var(--ge-primary);
}
</style>
