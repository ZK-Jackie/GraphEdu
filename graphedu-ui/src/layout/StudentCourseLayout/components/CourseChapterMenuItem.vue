<script setup lang="ts">
import { BookOutlined } from '@ant-design/icons-vue'
import type { ChapterTreeVO } from '@/types/api/chapter.ts'

/**
 * 章节菜单项，支持递归渲染子章节
 */
const props = defineProps<{
  chapter: ChapterTreeVO
}>()
</script>

<template>
  <!-- 有子章节：渲染 sub-menu -->
  <a-sub-menu v-if="chapter.children?.length" :key="`sub-${chapter.chapterId}`">
    <template #title>
      <span class="chapter-item-title">
        <BookOutlined class="mr-1.5 text-xs" />
        {{ chapter.chapterName }}
      </span>
    </template>
    <!-- 递归渲染子章节 -->
    <CourseChapterMenuItem v-for="child in chapter.children" :key="`chapter-${child.chapterId}`" :chapter="child" />
  </a-sub-menu>

  <!-- 叶子节点：渲染 menu-item -->
  <a-menu-item v-else :key="`chapter-${chapter.chapterId}`">
    <template #icon>
      <BookOutlined class="text-xs" />
    </template>
    <span class="chapter-item-title" :title="chapter.chapterName">
      {{ chapter.chapterName }}
    </span>
  </a-menu-item>
</template>

<style scoped>
.chapter-item-title {
  font-size: 0.875rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 160px;
  display: inline-block;
}
</style>
