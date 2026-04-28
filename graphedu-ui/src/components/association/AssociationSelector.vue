<template>
  <a-modal
    :visible="visible"
    :title="title"
    :width="800"
    :confirm-loading="loading"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <a-space direction="vertical" style="width: 100%">
      <!-- 搜索框 -->
      <a-input-search
        v-model:value="searchText"
        :placeholder="searchPlaceholder"
        enter-button
        @search="handleSearch"
        style="margin-bottom: 16px"
      />

      <!-- 可选项列表 -->
      <a-table
        :data-source="filteredItems"
        :loading="loading"
        :row-selection="rowSelection"
        :pagination="pagination"
        row-key="id"
        :scroll="{ y: 400 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            {{ record.name }}
          </template>
          <template v-else-if="column.key === 'description'">
            {{ record.description }}
          </template>
        </template>
      </a-table>
    </a-space>
  </a-modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

interface AssociationItem {
  id: string | number
  name: string
  description?: string
  [key: string]: any
}

interface Props {
  visible: boolean
  title?: string
  items: AssociationItem[]
  selectedIds: (string | number)[]
  searchPlaceholder?: string
  loading?: boolean
  multiple?: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'update:selectedIds', value: (string | number)[]): void
  (e: 'confirm', selectedIds: (string | number)[]): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  title: '选择关联项',
  searchPlaceholder: '搜索...',
  loading: false,
  multiple: true,
})

const emit = defineEmits<Emits>()

const searchText = ref('')
const selectedRowKeys = ref<(string | number)[]>([])

// 监听外部 selectedIds 变化
watch(
  () => props.selectedIds,
  (newIds) => {
    selectedRowKeys.value = [...newIds]
  },
  { immediate: true }
)

// 过滤后的项目
const filteredItems = computed(() => {
  if (!searchText.value) {
    return props.items
  }
  const searchLower = searchText.value.toLowerCase()
  return props.items.filter(
    (item) =>
      item.name.toLowerCase().includes(searchLower) ||
      (item.description && item.description.toLowerCase().includes(searchLower))
  )
})

// 分页配置
const pagination = computed(() => ({
  pageSize: 10,
  showSizeChanger: false,
  showTotal: (total: number) => `共 ${total} 项`,
}))

// 行选择配置
const rowSelection = computed(() => {
  if (!props.multiple) {
    return {
      type: 'radio' as const,
      selectedRowKeys: selectedRowKeys.value,
      onChange: (keys: (string | number)[]) => {
        selectedRowKeys.value = keys
      },
    }
  }
  return {
    selectedRowKeys: selectedRowKeys.value,
    onChange: (keys: (string | number)[]) => {
      selectedRowKeys.value = keys
    },
  }
})

// 搜索处理
const handleSearch = () => {
  // 搜索逻辑已在 computed 中处理
}

// 确认
const handleOk = () => {
  emit('update:selectedIds', selectedRowKeys.value)
  emit('confirm', selectedRowKeys.value)
  emit('update:visible', false)
  searchText.value = ''
}

// 取消
const handleCancel = () => {
  emit('cancel')
  emit('update:visible', false)
  searchText.value = ''
  // 重置为初始选中项
  selectedRowKeys.value = [...props.selectedIds]
}
</script>

<style scoped>
:deep(.ant-table) {
  font-size: 14px;
}
</style>
