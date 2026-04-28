<template>
  <div class="association-list">
    <a-table :data-source="items" :loading="loading" :pagination="pagination" row-key="id" :scroll="{ y: 400 }">
      <!-- 序号列 -->
      <a-table-column key="sort" title="序号" :width="80" align="center">
        <template #default="{ index }">
          {{ index + 1 }}
        </template>
      </a-table-column>

      <!-- 名称列 -->
      <a-table-column key="name" title="名称" data-index="name" :min-width="200" />

      <!-- 描述列（可选） -->
      <a-table-column v-if="showDescription" key="description" title="描述" data-index="description" :min-width="300" />

      <!-- 状态列（可选） -->
      <a-table-column v-if="showStatus" key="status" title="状态" data-index="status" :width="100" align="center">
        <template #default="{ record }">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
        </template>
      </a-table-column>

      <!-- 操作列 -->
      <a-table-column key="action" title="操作" :width="actionWidth" :fixed="actionFixed" align="center">
        <template #default="{ record }">
          <a-space>
            <a-button v-if="showEdit" type="link" size="small" @click="$emit('edit', record)"> 编辑 </a-button>
            <a-button v-if="showDelete" type="link" size="small" danger @click="$emit('delete', record)">
              删除
            </a-button>
            <a-button v-if="showUnlink" type="link" size="small" @click="$emit('unlink', record)"> 解除关联 </a-button>
          </a-space>
        </template>
      </a-table-column>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface AssociationListItem {
  id: string | number
  name: string
  description?: string
  status?: string
  [key: string]: any
}

interface Props {
  items: AssociationListItem[]
  loading?: boolean
  showDescription?: boolean
  showStatus?: boolean
  showEdit?: boolean
  showDelete?: boolean
  showUnlink?: boolean
  pageSize?: number
  actionWidth?: number
  actionFixed?: 'left' | 'right' | boolean
}

interface Emits {
  (e: 'edit', item: AssociationListItem): void
  (e: 'delete', item: AssociationListItem): void
  (e: 'unlink', item: AssociationListItem): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  showDescription: true,
  showStatus: false,
  showEdit: false,
  showDelete: false,
  showUnlink: true,
  pageSize: 10,
  actionWidth: 150,
  actionFixed: false,
})

defineEmits<Emits>()

// 分页配置
const pagination = computed(() => ({
  pageSize: props.pageSize,
  showSizeChanger: false,
  showTotal: (total: number) => `共 ${total} 项`,
}))

// 获取状态颜色
const getStatusColor = (status: string) => {
  const statusMap: Record<string, string> = {
    '0': 'green', // 正常
    '1': 'red', // 停用
    '2': 'default', // 删除
    normal: 'green',
    disabled: 'red',
    deleted: 'default',
  }
  return statusMap[status] || 'default'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    '0': '正常',
    '1': '停用',
    '2': '已删除',
    normal: '正常',
    disabled: '停用',
    deleted: '已删除',
  }
  return statusMap[status] || status
}
</script>

<style scoped>
.association-list {
  width: 100%;
}

:deep(.ant-table) {
  font-size: 14px;
}

:deep(.ant-table-cell) {
  padding: 8px 12px;
}
</style>
