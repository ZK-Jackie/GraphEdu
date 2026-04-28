<script setup lang="ts">
/**
 * SemanticGraphTaskList - 语义知识图谱任务列表
 *
 * 功能：
 * - Tab 状态过滤（全部/运行中/已完成/已启用）
 * - 任务表格，操作列使用下拉菜单
 * - 空状态引导
 * - 行展开摘要
 */
import { computed, ref } from 'vue'
import { Modal, message } from 'ant-design-vue'
import { EllipsisOutlined, PlusOutlined } from '@ant-design/icons-vue'
import type { MenuProps } from 'ant-design-vue'

import type { GraphRAGTaskListVO } from '@/types/api/education/graphragTask.ts'

interface Props {
  taskList: GraphRAGTaskListVO[]
  loading: boolean
  retryingTaskId: number | null
  cancelingTaskId: number | null
}

interface Emits {
  (e: 'enable', taskId: number): void
  (e: 'cancel', taskId: number): void
  (e: 'retry', taskId: number): void
  (e: 'delete', taskId: number): void
  (e: 'view-progress', record: GraphRAGTaskListVO): void
  (e: 'view-detail', record: GraphRAGTaskListVO): void
  (e: 'create'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// ─── Tab 过滤 ─────────────────────────────────────────────────────────────────

const activeTab = ref('all')

const tabCounts = computed(() => {
  const list = props.taskList
  return {
    all: list.length,
    running: list.filter((t) => isRunningStatus(t.taskStatus)).length,
    finished: list.filter((t) => !isRunningStatus(t.taskStatus)).length,
    enabled: list.filter((t) => t.enabled === 'Y').length,
  }
})

const filteredList = computed(() => {
  const list = props.taskList
  switch (activeTab.value) {
    case 'running':
      return list.filter((t) => isRunningStatus(t.taskStatus))
    case 'finished':
      return list.filter((t) => !isRunningStatus(t.taskStatus))
    case 'enabled':
      return list.filter((t) => t.enabled === 'Y')
    default:
      return list
  }
})

// ─── 状态映射 ─────────────────────────────────────────────────────────────────

const statusTextMap: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  success: '成功',
  failed: '失败',
  cancelled: '已取消',
}

const statusColorMap: Record<string, string> = {
  pending: 'default',
  processing: 'processing',
  success: 'success',
  failed: 'error',
  cancelled: 'warning',
}

function isRunningStatus(status?: string): boolean {
  return status === 'pending' || status === 'processing'
}

function isRetryableStatus(status?: string): boolean {
  return status === 'failed' || status === 'cancelled'
}

// ─── 表格列 ───────────────────────────────────────────────────────────────────

const columns = [
  { title: '#', dataIndex: 'taskId', key: 'taskId', width: 60 },
  { title: '状态', dataIndex: 'taskStatus', key: 'taskStatus', width: 100 },
  { title: '启用', dataIndex: 'enabled', key: 'enabled', width: 80 },
  { title: '资源', key: 'resourceCount', width: 80, align: 'center' as const },
  { title: '实体类型', key: 'entityTypes', width: 180 },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 170 },
  { title: '操作', key: 'action', width: 60, fixed: 'right' as const },
]

// ─── 展开行 ───────────────────────────────────────────────────────────────────

const expandedRowKeys = ref<number[]>([])

function handleExpand(expanded: boolean, record: GraphRAGTaskListVO) {
  if (expanded) {
    expandedRowKeys.value = [record.taskId]
  } else {
    expandedRowKeys.value = expandedRowKeys.value.filter((id) => id !== record.taskId)
  }
}

// ─── 下拉菜单操作 ─────────────────────────────────────────────────────────────

function getActionMenuItems(record: GraphRAGTaskListVO) {
  const items: NonNullable<MenuProps['items']> = []

  items.push({ key: 'detail', label: '查看详情' })

  if (isRunningStatus(record.taskStatus)) {
    items.push({ key: 'progress', label: '查看进度' })
    items.push({ type: 'divider' })
    items.push({ key: 'cancel', label: '取消任务', danger: true })
  }

  if (record.taskStatus === 'success') {
    if (record.enabled !== 'Y') {
      items.push({ key: 'enable', label: '启用' })
    }
    items.push({ key: 'rebuild', label: '重建' })
    items.push({ type: 'divider' })
    items.push({ key: 'delete', label: '删除', danger: true })
  }

  if (isRetryableStatus(record.taskStatus)) {
    items.push({ key: 'retry', label: '重试' })
    items.push({ type: 'divider' })
    items.push({ key: 'delete', label: '删除', danger: true })
  }

  return items
}

function handleActionClick({ key }: { key: string }, record: GraphRAGTaskListVO) {
  const taskId = record.taskId
  switch (key) {
    case 'detail':
      emit('view-detail', record)
      break
    case 'progress':
      emit('view-progress', record)
      break
    case 'enable':
      emit('enable', taskId)
      break
    case 'rebuild':
    case 'retry':
      emit('retry', taskId)
      break
    case 'cancel':
      Modal.confirm({
        title: '确认取消任务',
        content: `将取消任务 #${taskId}，是否继续？`,
        okText: '确认',
        cancelText: '返回',
        onOk: () => emit('cancel', taskId),
      })
      break
    case 'delete':
      Modal.confirm({
        title: '确认删除',
        content: `将删除任务 #${taskId}，是否继续？`,
        okText: '确认',
        cancelText: '返回',
        onOk: () => emit('delete', taskId),
      })
      break
  }
}

// ─── 格式化时间 ───────────────────────────────────────────────────────────────

function formatDateTime(dateStr?: string) {
  if (!dateStr) return '-'
  return dateStr
}
</script>

<template>
  <div class="task-list-wrapper">
    <a-tabs v-model:activeKey="activeTab" class="status-tabs">
      <a-tab-pane key="all">
        <template #tab>
          全部 <a-badge :count="tabCounts.all" :number-style="{ backgroundColor: '#8c8c8c' }" />
        </template>
      </a-tab-pane>
      <a-tab-pane key="running">
        <template #tab>
          运行中
          <a-badge
            v-if="tabCounts.running > 0"
            :count="tabCounts.running"
            :number-style="{ backgroundColor: '#fa8c16' }"
          />
        </template>
      </a-tab-pane>
      <a-tab-pane key="finished">
        <template #tab> 已完成 </template>
      </a-tab-pane>
      <a-tab-pane key="enabled">
        <template #tab>
          已启用
          <a-badge
            v-if="tabCounts.enabled > 0"
            :count="tabCounts.enabled"
            :number-style="{ backgroundColor: '#52c41a' }"
          />
        </template>
      </a-tab-pane>
    </a-tabs>

    <a-table
      row-key="taskId"
      size="small"
      :columns="columns"
      :data-source="filteredList"
      :loading="loading"
      :pagination="false"
      :scroll="{ x: 'max-content' }"
      :expanded-row-keys="expandedRowKeys"
      :expandable="{
        expandedRowRender: undefined as any,
        onExpand: handleExpand,
        onExpandedRowsChange: () => {},
      }"
    >
      <!-- 展开行内容 -->
      <template #expandedRowRender="{ record }">
        <div class="expand-content">
          <div class="expand-section">
            <span class="expand-label">资源ID：</span>
            <div class="expand-tags">
              <a-tag v-for="id in (record.resourceIds || []).slice(0, 10)" :key="id" size="small">{{ id }}</a-tag>
              <span v-if="(record.resourceIds || []).length > 10" class="expand-more">
                +{{ (record.resourceIds || []).length - 10 }}
              </span>
              <span v-if="!record.resourceIds?.length" class="expand-empty">-</span>
            </div>
          </div>
          <div class="expand-section">
            <span class="expand-label">实体类型：</span>
            <div class="expand-tags">
              <a-tag v-for="et in record.entityTypes || []" :key="et" color="blue" size="small">{{ et }}</a-tag>
              <span v-if="!record.entityTypes?.length" class="expand-empty">-</span>
            </div>
          </div>
          <div v-if="record.stats && Object.keys(record.stats).length" class="expand-section">
            <span class="expand-label">统计：</span>
            <div class="expand-tags">
              <template v-for="(value, key) in record.stats" :key="String(key)">
                <a-tag size="small">{{ key }}: {{ value }}</a-tag>
              </template>
            </div>
          </div>
        </div>
      </template>

      <!-- 状态列 -->
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'taskStatus'">
          <span class="status-cell">
            <span
              class="status-dot"
              :class="{
                'status-dot--processing': record.taskStatus === 'processing',
                'status-dot--pending': record.taskStatus === 'pending',
              }"
              :style="{
                backgroundColor:
                  record.taskStatus === 'success'
                    ? '#52c41a'
                    : record.taskStatus === 'failed'
                      ? '#ff4d4f'
                      : record.taskStatus === 'cancelled'
                        ? '#faad14'
                        : record.taskStatus === 'processing'
                          ? '#1677ff'
                          : '#d9d9d9',
              }"
            />
            <span>{{ statusTextMap[record.taskStatus] || record.taskStatus }}</span>
          </span>
        </template>

        <!-- 启用列 -->
        <template v-else-if="column.key === 'enabled'">
          <span v-if="record.enabled === 'Y'" class="enabled-badge">已启用</span>
          <span v-else class="disabled-badge">-</span>
        </template>

        <!-- 资源数量列 -->
        <template v-else-if="column.key === 'resourceCount'">
          {{ record.resourceIds?.length || 0 }}
        </template>

        <!-- 实体类型列 -->
        <template v-else-if="column.key === 'entityTypes'">
          <template v-if="record.entityTypes?.length">
            <a-tag v-for="et in record.entityTypes.slice(0, 2)" :key="et" size="small">{{ et }}</a-tag>
            <span v-if="record.entityTypes.length > 2" class="expand-more"> +{{ record.entityTypes.length - 2 }} </span>
          </template>
          <span v-else class="expand-empty">-</span>
        </template>

        <!-- 时间列 -->
        <template v-else-if="column.key === 'createTime'">
          {{ formatDateTime(record.createTime) }}
        </template>

        <!-- 操作列 -->
        <template v-else-if="column.key === 'action'">
          <a-dropdown :trigger="['click']">
            <a-button type="text" size="small" class="action-btn">
              <template #icon><EllipsisOutlined /></template>
            </a-button>
            <template #overlay>
              <a-menu
                :items="getActionMenuItems(record as GraphRAGTaskListVO)"
                @click="(info: any) => handleActionClick(info, record as GraphRAGTaskListVO)"
              />
            </template>
          </a-dropdown>
        </template>
      </template>
    </a-table>

    <!-- 空状态 -->
    <div v-if="!loading && filteredList.length === 0" class="empty-state">
      <a-empty :description="activeTab === 'all' ? '暂无构建任务' : '该分类下暂无任务'">
        <a-button v-if="activeTab === 'all' && taskList.length === 0" type="primary" @click="$emit('create')">
          <template #icon><PlusOutlined /></template>
          新建图谱
        </a-button>
      </a-empty>
    </div>
  </div>
</template>

<style scoped>
@reference '#main.css';

.task-list-wrapper {
  @apply flex flex-col;
}

/* Tab 样式微调 */
.status-tabs {
  @apply mb-2;
}

:deep(.ant-tabs-nav) {
  margin-bottom: 0;
}

/* 状态指示器 */
.status-cell {
  @apply inline-flex items-center gap-1.5;
}

.status-dot {
  @apply w-2 h-2 rounded-full flex-shrink-0;
}

.status-dot--processing {
  animation: pulse-dot 1.5s ease-in-out infinite;
}

.status-dot--pending {
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}

/* 启用/禁用 */
.enabled-badge {
  @apply text-xs font-medium text-green-600 dark:text-green-400;
}

.disabled-badge {
  @apply text-xs text-gray-400;
}

/* 操作按钮 */
.action-btn {
  @apply flex items-center justify-center;
}

/* 展开行 */
.expand-content {
  @apply flex flex-col gap-2 py-2 px-4;
}

.expand-section {
  @apply flex items-start gap-2;
}

.expand-label {
  @apply text-xs text-gray-500 dark:text-gray-400 flex-shrink-0 pt-0.5;
}

.expand-tags {
  @apply flex flex-wrap gap-1;
}

.expand-more {
  @apply text-xs text-gray-400 ml-1;
}

.expand-empty {
  @apply text-xs text-gray-400;
}

/* 空状态 */
.empty-state {
  @apply flex items-center justify-center py-12;
}
</style>
