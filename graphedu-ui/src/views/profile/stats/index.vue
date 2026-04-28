<template>
  <a-card :bordered="true">
    <template #title>
      <span>学习统计</span>
    </template>

    <div class="stats-content">
      <a-result status="info" title="功能开发中" sub-title="学习统计功能正在开发中，敬请期待...">
        <template #extra>
          <a-space>
            <a-button type="primary">了解更多</a-button>
            <a-button>联系客服</a-button>
          </a-space>
        </template>
      </a-result>
    </div>
  </a-card>
</template>

<script setup lang="ts">
// 学习统计页面
// 功能待开发
</script>

<style scoped>
.stats-content {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
