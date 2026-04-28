<template>
  <div class="knowledge-point-tab">
    <!-- 操作栏 -->
    <div class="toolbar">
      <a-space>
        <a-button type="primary" @click="selectorVisible = true">
          <template #icon><PlusOutlined /></template>
          关联知识点
        </a-button>
        <a-button @click="loadKnowledgePoints">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
      </a-space>
    </div>

    <!-- 知识点列表 -->
    <a-table
      :data-source="knowledgePoints"
      :loading="loading"
      :pagination="pagination"
      row-key="nodeChapterId"
      :scroll="{ y: 400 }"
    >
      <a-table-column key="sort" title="序号" :width="80" align="center">
        <template #default="{ index }">{{ index + 1 }}</template>
      </a-table-column>
      <a-table-column key="nodeTitle" title="知识点名称" data-index="nodeTitle" />
      <a-table-column key="nodeDescription" title="描述" data-index="nodeDescription" />
      <a-table-column key="nodeImportance" title="重要性" data-index="nodeImportance" :width="120" align="center">
        <template #default="{ record }">
          <a-tag v-if="record.nodeImportance" :color="getImportanceColor(record.nodeImportance)">
            {{ record.nodeImportance }}
          </a-tag>
        </template>
      </a-table-column>
      <a-table-column key="action" title="操作" :width="100" align="center">
        <template #default="{ record }">
          <a-button type="link" size="small" danger @click="handleUnlink(record)"> 解除关联 </a-button>
        </template>
      </a-table-column>
    </a-table>

    <!-- 知识点选择器对话框 -->
    <KnowledgePointSelector
      v-model:visible="selectorVisible"
      :chapter-id="chapterId"
      :selected-ids="selectedPointIds"
      @success="handleLinkSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { getChapterKnowledgePoints, unlinkChapterKnowledgePoint } from '@/api/education/chapter.ts'
import KnowledgePointSelector from './KnowledgePointSelector.vue'
import type { KnowledgeNodeChapterDetailVO } from '@/types/api/education/knowledgeGraph.ts'

interface Props {
  chapterId: number
}

const props = defineProps<Props>()

const loading = ref(false)
const knowledgePoints = ref<KnowledgeNodeChapterDetailVO[]>([])
const selectorVisible = ref(false)

// 已选中的知识点 ID 列表
const selectedPointIds = computed(() => knowledgePoints.value.map((kp) => kp.nodeUuid))

// 分页配置
const pagination = computed(() => ({
  pageSize: 20,
  showSizeChanger: false,
  showTotal: (total: number) => `共 ${total} 项`,
}))

// 加载知识点列表
const loadKnowledgePoints = async () => {
  if (!props.chapterId) return

  loading.value = true
  try {
    const res = await getChapterKnowledgePoints(props.chapterId)
    if (res.code === 200) {
      knowledgePoints.value = res.data || []
    }
  } catch (_e) {
    message.error('加载知识点列表失败')
  } finally {
    loading.value = false
  }
}

// 解除关联
const handleUnlink = async (record: KnowledgeNodeChapterDetailVO) => {
  try {
    const res = await unlinkChapterKnowledgePoint(props.chapterId, record.nodeUuid)
    if (res.code === 200) {
      message.success('解除关联成功')
      await loadKnowledgePoints()
    }
  } catch (_e) {
    message.error('解除关联失败')
  }
}

// 关联成功回调
const handleLinkSuccess = () => {
  loadKnowledgePoints()
}

// 获取重要性颜色
const getImportanceColor = (importance: string) => {
  const colors: Record<string, string> = {
    high: 'red',
    medium: 'orange',
    low: 'green',
    高: 'red',
    中: 'orange',
    低: 'green',
  }
  return colors[importance] || 'default'
}

// 监听 chapterId 变化
watch(
  () => props.chapterId,
  (newId) => {
    if (newId) {
      loadKnowledgePoints()
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.knowledge-point-tab {
  width: 100%;
}

.toolbar {
  margin-bottom: 16px;
}
</style>
