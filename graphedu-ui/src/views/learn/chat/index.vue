<template>
  <div class="learn-chat-page">
    <a-page-header title="问答历史" sub-title="查看AI问答交互记录" />

    <a-card :bordered="false">
      <a-result status="info" title="页面开发中" sub-title="问答历史功能正在开发中，敬请期待...">
        <template #extra>
          <a-button type="primary" @click="goBack">返回</a-button>
        </template>
      </a-result>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const pageTitle = computed(() => '问答历史')
const pageDescription = computed(() => '查看AI问答交互记录')

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.learn-chat-page {
  padding: 16px;
}
</style>
