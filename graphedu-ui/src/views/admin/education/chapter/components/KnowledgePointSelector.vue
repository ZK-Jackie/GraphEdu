<template>
  <a-modal
    :visible="visible"
    title="选择知识点"
    :width="800"
    :confirm-loading="loading"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <a-space direction="vertical" style="width: 100%">
      <!-- 搜索框 -->
      <a-input-search
        v-model:value="searchText"
        placeholder="搜索知识点..."
        enter-button
        @search="handleSearch"
        style="margin-bottom: 16px"
      />

      <!-- 知识点列表 -->
      <a-table
        :data-source="filteredKnowledgePoints"
        :loading="loading"
        :row-selection="rowSelection as any"
        :pagination="pagination"
        row-key="id"
        :scroll="{ y: 400 }"
      >
        <a-table-column key="title" title="知识点名称" data-index="title" />
        <a-table-column key="description" title="描述" data-index="description" />
        <a-table-column key="importance" title="重要性" data-index="importance" :width="120" align="center">
          <template #default="{ record }">
            <a-tag v-if="record.importance" :color="getImportanceColor(record.importance)">
              {{ record.importance }}
            </a-tag>
          </template>
        </a-table-column>
      </a-table>
    </a-space>
  </a-modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import type { TableProps } from 'ant-design-vue'
import { linkChapterKnowledgePoints } from '@/api/education/chapter.ts'

interface Props {
  visible: boolean
  chapterId: number
  selectedIds?: string[]
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

interface KnowledgePointNode {
  id: string
  title: string
  description?: string
  importance?: string
}

const props = withDefaults(defineProps<Props>(), {
  selectedIds: () => [],
})

const emit = defineEmits<Emits>()

const loading = ref(false)
const searchText = ref('')
const selectedRowKeys = ref<string[]>([])
const allKnowledgePoints = ref<KnowledgePointNode[]>([])

// 模拟知识点数据（实际应从知识图谱 API 获取）
// TODO: 替换为真实的知识图谱 API 调用
const mockKnowledgePoints: KnowledgePointNode[] = [
  { id: 'node1', title: '函数', description: '数学函数的基本概念', importance: 'high' },
  { id: 'node2', title: '导数', description: '导数的定义和性质', importance: 'high' },
  { id: 'node3', title: '积分', description: '积分的基本概念', importance: 'medium' },
  { id: 'node4', title: '极限', description: '极限的定义和计算', importance: 'medium' },
  { id: 'node5', title: '微分方程', description: '微分方程的解法', importance: 'low' },
]

// 过滤后的知识点
const filteredKnowledgePoints = computed(() => {
  const points = allKnowledgePoints.value.length > 0 ? allKnowledgePoints.value : mockKnowledgePoints

  if (!searchText.value) {
    return points
  }

  const searchLower = searchText.value.toLowerCase()
  return points.filter(
    (point) =>
      point.title.toLowerCase().includes(searchLower) ||
      (point.description && point.description.toLowerCase().includes(searchLower))
  )
})

// 分页配置
const pagination = computed(() => ({
  pageSize: 10,
  showSizeChanger: false,
  showTotal: (total: number) => `共 ${total} 项`,
}))

// 行选择配置
const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: string[]) => {
    selectedRowKeys.value = keys
  },
}) as any)

// 搜索处理
const handleSearch = () => {
  // 搜索逻辑已在 computed 中处理
}

// 确认
const handleOk = async () => {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请选择要关联的知识点')
    return
  }

  loading.value = true
  try {
    const res = await linkChapterKnowledgePoints(props.chapterId, {
      pointIds: selectedRowKeys.value,
    })

    if (res.code === 200) {
      message.success('关联成功')
      emit('success')
      emit('update:visible', false)
      selectedRowKeys.value = []
      searchText.value = ''
    }
  } catch (_e) {
    message.error('关联失败')
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  emit('update:visible', false)
  searchText.value = ''
  selectedRowKeys.value = [...props.selectedIds]
}

// 获取重要性颜色
const getImportanceColor = (importance: string) => {
  const colors: Record<string, string> = {
    high: 'red',
    medium: 'orange',
    low: 'green',
  }
  return colors[importance] || 'default'
}

// 监听 visible 变化，加载知识点数据
watch(
  () => props.visible,
  (newVisible) => {
    if (newVisible) {
      // TODO: 从知识图谱 API 加载知识点数据
      // allKnowledgePoints.value = await fetchKnowledgePoints()
      selectedRowKeys.value = [...props.selectedIds]
    }
  }
)
</script>

<style scoped>
:deep(.ant-table) {
  font-size: 14px;
}
</style>
