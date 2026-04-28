<script setup lang="ts">
/**
 * 隐私政策页面
 */
import CommonPageLayout from '@/layout/CommonPageLayout.vue'
</script>

<template>
  <CommonPageLayout title="隐私政策">
    <div class="article-content">
      <p class="update-date">最后更新日期：2026 年 4 月</p>

      <h3>信息收集</h3>
      <p>我们可能收集以下类型的信息以提供和改善服务：</p>
      <ul>
        <li><strong>账户信息</strong> — 注册时提供的用户名、密码（加密存储）、学号或工号</li>
        <li><strong>学习数据</strong> — 学习进度、答题记录、知识点掌握情况</li>
        <li><strong>使用数据</strong> — 页面访问记录、功能使用频率、浏览器类型</li>
      </ul>

      <h3>信息使用</h3>
      <p>收集的信息仅用于以下目的：</p>
      <ul>
        <li>提供个性化学习体验和智能推荐</li>
        <li>分析学习行为，优化教学内容和路径</li>
        <li>平台运维与安全防护</li>
      </ul>

      <h3>信息保护</h3>
      <p>
        我们采用行业标准的安全措施保护您的个人信息，包括数据加密传输（HTTPS）、密码哈希存储、访问权限控制等。
        数据存储在受保护的服务器上，仅授权人员可以访问。
      </p>

      <h3>信息共享</h3>
      <p>我们不会将您的个人信息出售或共享给第三方。学习数据可能匿名化后用于教学研究和平台优化。</p>

      <h3>您的权利</h3>
      <p>您有权查看、修改或删除您的个人信息。如有需求，请通过平台内联系功能与管理员取得联系。</p>
    </div>
  </CommonPageLayout>
</template>

<style scoped>
@reference '#main.css';

.article-content {
  @apply max-w-3xl mx-auto;
}

.update-date {
  @apply text-xs mb-6;
  color: var(--ge-text-tertiary);
}

.article-content :deep(h3) {
  @apply text-lg font-semibold mt-8 mb-3;
  color: var(--ge-text-primary);
}

.article-content :deep(p) {
  @apply mb-4 leading-relaxed text-sm;
  color: var(--ge-text-secondary);
}

.article-content :deep(ul) {
  @apply mb-4 pl-5;
  list-style: disc;
}

.article-content :deep(li) {
  @apply mb-2 text-sm leading-relaxed;
  color: var(--ge-text-secondary);
}

.article-content :deep(strong) {
  color: var(--ge-text-primary);
}
</style>
