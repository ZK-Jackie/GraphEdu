<template>
  <a-modal v-model:open="visible" title="选择图标" :width="900" :footer="null" @cancel="handleCancel">
    <!-- 搜索框 -->
    <a-input v-model:value="searchText" placeholder="搜索图标名称" allow-clear size="large">
      <template #prefix>
        <SearchOutlined :style="{ color: 'var(--ge-text-tertiary)' }" />
      </template>
    </a-input>

    <!-- 分类标签 -->
    <a-tabs v-model:active-key="activeTab" class="mt-4" size="large">
      <a-tab-pane key="all" tab="全部">
        <template #tab>
          <span>全部</span>
          <a-badge :count="allIconIds.length" :number-style="{ backgroundColor: '#52c41a', marginLeft: '8px' }" />
        </template>
      </a-tab-pane>
      <a-tab-pane key="outlined" tab="描边" />
      <a-tab-pane key="filled" tab="填充" />
      <a-tab-pane key="twotone" tab="双色" />
    </a-tabs>

    <!-- 图标网格 -->
    <div class="icon-grid-wrapper">
      <div class="icon-grid">
        <div
          v-for="iconId in filteredIcons"
          :key="iconId"
          class="icon-item"
          :class="{ 'icon-item--selected': iconId === selectedIcon }"
          :title="iconId"
          @click="selectIcon(iconId)"
        >
          <SvgIcon :icon="iconId" :size="24" />
          <div class="icon-name">{{ iconId }}</div>
        </div>
      </div>
      <a-empty v-if="filteredIcons.length === 0" description="暂无匹配图标" class="mt-8" />
    </div>

    <!-- 底部操作 -->
    <div class="icon-footer">
      <div class="icon-preview">
        <template v-if="selectedIcon">
          <div class="icon-preview-box">
            <SvgIcon :icon="selectedIcon" :size="32" />
          </div>
          <span class="icon-preview-name">{{ selectedIcon }}</span>
        </template>
        <span v-else class="icon-preview-hint">请选择一个图标</span>
      </div>
      <div class="icon-actions">
        <a-button @click="handleCancel">取消</a-button>
        <a-button type="primary" :disabled="!selectedIcon" @click="handleOk">确定</a-button>
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { SearchOutlined } from '@ant-design/icons-vue'
import allIconIds from 'virtual:svg-icons-client'

interface Props {
  modelValue?: string
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const visible = ref(false)
const searchText = ref('')
const activeTab = ref<string>('all')
const selectedIcon = ref<string>('')

// 过滤图标
const filteredIcons = computed(() => {
  let icons = [...allIconIds]

  // 风格过滤 - 图标 ID 格式为 icon-{style}-{name}
  if (activeTab.value !== 'all') {
    icons = icons.filter((id) => id.includes(`-${activeTab.value}-`))
  }

  // 搜索过滤
  if (searchText.value.trim()) {
    const search = searchText.value.toLowerCase().trim()
    icons = icons.filter((id) => id.toLowerCase().includes(search))
  }

  return icons
})

// 选择图标
const selectIcon = (iconId: string) => {
  selectedIcon.value = iconId
}

// 打开弹窗
watch(
  () => visible.value,
  (val) => {
    if (val) {
      selectedIcon.value = props.modelValue ?? ''
      searchText.value = ''
      activeTab.value = 'all'
    }
  }
)

// 确定
const handleOk = () => {
  emit('update:modelValue', selectedIcon.value)
  emit('change', selectedIcon.value)
  visible.value = false
}

// 取消
const handleCancel = () => {
  visible.value = false
}

// 暴露方法：打开选择器
defineExpose({
  open: () => {
    visible.value = true
  },
})
</script>

<style scoped>
.icon-grid-wrapper {
  max-height: 450px;
  overflow-y: auto;
}

.icon-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
  padding: 12px 0;
  margin-top: 16px;
}

.icon-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 8px;
  border: 1px solid var(--ge-border-color);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 80px;
}

.icon-item:hover {
  border-color: var(--ge-primary);
  background-color: var(--ge-primary-light);
  transform: translateY(-2px);
  box-shadow: 0 2px 8px color-mix(in srgb, var(--ge-primary) 15%, transparent);
}

.icon-item--selected {
  border-color: var(--ge-primary);
  background-color: var(--ge-primary-focus);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--ge-primary) 20%, transparent);
}

.icon-name {
  font-size: 11px;
  color: var(--ge-text-secondary);
  margin-top: 8px;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
}

.icon-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  margin-top: 16px;
  border-top: 1px solid var(--ge-border-color);
}

.icon-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.icon-preview-box {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border: 1px solid var(--ge-border-color);
  border-radius: 6px;
  background-color: var(--ge-bg-elevated);
}

.icon-preview-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--ge-text-primary);
}

.icon-preview-hint {
  font-size: 14px;
  color: var(--ge-text-tertiary);
}

.icon-actions {
  display: flex;
  gap: 8px;
}
</style>
