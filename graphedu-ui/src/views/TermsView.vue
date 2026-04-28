<script setup lang="ts">
/**
 * 使用条款页面
 */
import CommonPageLayout from '@/layout/CommonPageLayout.vue'
</script>

<template>
  <CommonPageLayout title="使用条款">
    <div class="article-content">
      <p class="update-date">最后更新日期：2026 年 4 月</p>

      <h3>服务说明</h3>
      <p>智图学堂是一个面向教育场景的知识图谱学习平台。本平台仅供学习和研究使用，不构成任何商业服务承诺。</p>

      <h3>用户行为规范</h3>
      <ul>
        <li>注册时提供真实、准确的信息</li>
        <li>妥善保管账户凭证，不得将账户借予他人使用</li>
        <li>不得利用平台从事违法、违规或侵害他人权益的活动</li>
        <li>不得通过技术手段恶意访问或破坏平台系统</li>
      </ul>

      <h3>知识产权</h3>
      <p>
        平台上的课程内容、知识图谱数据、文档资料等知识产权归原作者或平台所有。 未经授权，不得复制、传播或用于商业目的。
      </p>

      <h3>免责声明</h3>
      <p>
        本平台为教育研究项目，按"现状"提供服务。我们不保证服务的不间断运行或完全无错误。
        对于因使用本平台而产生的任何直接或间接损失，我们不承担责任。
      </p>

      <h3>条款修改</h3>
      <p>我们保留随时修改本条款的权利。修改后的条款将在本页面更新，继续使用平台即视为接受修改后的条款。</p>
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
</style>
