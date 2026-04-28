<script setup lang="ts">
/**
 * 关于我们页面
 */
import CommonPageLayout from '@/layout/CommonPageLayout.vue'
</script>

<template>
  <CommonPageLayout title="关于我们">
    <div class="article-content">
      <h2>智图学堂</h2>
      <p>
        智图学堂是一个基于知识图谱的智能学习平台，旨在通过知识图谱技术帮助学生建立系统化的知识结构，结合人工智能提供个性化的学习路径推荐与智能答疑服务。
      </p>

      <h3>项目背景</h3>
      <p>
        本项目是毕业设计作品，探索知识图谱技术在教育领域的应用。通过将课程知识体系结构化为图谱，学生可以直观地理解知识点之间的关联关系，从而提升学习效率。
      </p>

      <h3>核心功能</h3>
      <ul>
        <li><strong>知识图谱可视化</strong> — 基于课程体系构建知识图谱，直观展示知识点之间的关联</li>
        <li><strong>AI 智能辅导</strong> — 基于 LangGraph 的智能辅导系统，支持个性化答疑与学习路径推荐</li>
        <li><strong>学习数据分析</strong> — 学习日历、趋势图表、薄弱知识点分析</li>
        <li><strong>多角色协同</strong> — 支持学生、教师、管理员多角色使用</li>
      </ul>

      <h3>技术栈</h3>
      <ul>
        <li>前端：Vue 3 + TypeScript + Ant Design Vue + Tailwind CSS</li>
        <li>后端：FastAPI + SQLAlchemy 2.0（异步）</li>
        <li>数据库：PostgreSQL + Redis + Neo4j</li>
        <li>AI：LangChain / LangGraph</li>
      </ul>
    </div>
  </CommonPageLayout>
</template>

<style scoped>
@reference '#main.css';

.article-content {
  @apply max-w-3xl mx-auto;
}

.article-content :deep(h2) {
  @apply text-xl font-bold mb-3;
  color: var(--ge-text-primary);
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
