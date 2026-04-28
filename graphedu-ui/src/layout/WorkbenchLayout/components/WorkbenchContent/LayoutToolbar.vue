<script setup lang="ts">
import { ref, inject } from 'vue'
import type GoldenLayout from '@/components/VueGoldenLayout/index.vue'

// 如果 WorkbenchContent 提供了 ref，可以直接操作布局
const layoutRef = inject<{ value: InstanceType<typeof GoldenLayout> | null }>('layoutRef', { value: null })

const currentLayout = ref('default')

// 预设布局配置（待实现）
const presetLayouts: Record<string, any> = {}

const switchLayout = async (layoutName: string) => {
  if (!layoutRef.value) {
    console.warn('Layout reference not available')
    return
  }

  currentLayout.value = layoutName
  const config = presetLayouts[layoutName]

  if (config) {
    await layoutRef.value.loadLayout(config)
  }
}

const saveLayout = () => {
  if (layoutRef.value) {
    const config = layoutRef.value.getLayoutConfig()
    localStorage.setItem('gl-layout', JSON.stringify(config))
  }
}

const loadSavedLayout = async () => {
  const saved = localStorage.getItem('gl-layout')
  if (saved && layoutRef.value) {
    try {
      const config = JSON.parse(saved)
      await layoutRef.value.loadLayout(config)
      currentLayout.value = 'custom'
    } catch (error) {
      console.error('加载保存的布局失败:', error)
    }
  }
}
</script>

<template>
  <div class="layout-toolbar">
    <div class="toolbar-section">
      <span class="toolbar-label">布局模板:</span>
      <select v-model="currentLayout" class="layout-select" @change="switchLayout(currentLayout)">
        <option value="default">默认布局</option>
        <option value="singleColumn">单列布局</option>
        <option value="threeColumns">三栏布局</option>
      </select>
    </div>

    <div class="toolbar-section">
      <button class="toolbar-btn" @click="saveLayout">💾 保存布局</button>
      <button class="toolbar-btn" @click="loadSavedLayout">📂 加载布局</button>
    </div>
  </div>
</template>

<style scoped>
.layout-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.5rem;
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.toolbar-section {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.toolbar-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.layout-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  background-color: white;
  cursor: pointer;
}

.layout-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.toolbar-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background-color: white;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s;
}

.toolbar-btn:hover {
  background-color: #f3f4f6;
  border-color: #9ca3af;
}

.toolbar-btn:active {
  transform: scale(0.98);
}

/* 暗色模式 */
.dark .layout-toolbar {
  background-color: #1f2937;
  border-bottom-color: #374151;
}

.dark .toolbar-label {
  color: #d1d5db;
}

.dark .layout-select,
.dark .toolbar-btn {
  background-color: #374151;
  border-color: #4b5563;
  color: #d1d5db;
}

.dark .layout-select:focus,
.dark .toolbar-btn:hover {
  background-color: #4b5563;
  border-color: #6b7280;
}
</style>
