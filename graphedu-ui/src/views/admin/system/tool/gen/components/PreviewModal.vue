<template>
  <a-modal v-model:open="visible" title="代码预览" width="80%" :footer="null" :destroy-on-close="true">
    <a-tabs v-model:active-key="activeTab">
      <a-tab-pane v-for="(code, fileName) in previewData" :key="getTabKey(fileName)" :tab="getTabLabel(fileName)">
        <div style="position: relative">
          <a-button
            type="link"
            size="small"
            style="position: absolute; right: 0; top: 0; z-index: 1"
            @click="copyCode(code, fileName)"
          >
            <template #icon><CopyOutlined /></template>
            复制
          </a-button>
          <pre
            style="
              margin: 0;
              padding: 16px;
              background: #f5f5f5;
              border-radius: 4px;
              overflow-x: auto;
              max-height: 500px;
              overflow-y: auto;
            "
            >{{ code }}</pre
          >
        </div>
      </a-tab-pane>
    </a-tabs>
  </a-modal>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import { CopyOutlined } from '@ant-design/icons-vue'
import type { GenCodePreviewVO } from '@/types/api/tool/gen.ts'

const visible = ref(false)
const activeTab = ref('domain.java')
const previewData = ref<GenCodePreviewVO>({})

/** 显示弹窗 */
function show(data: GenCodePreviewVO) {
  previewData.value = data
  visible.value = true
  // 设置默认激活的标签页
  const keys = Object.keys(data)
  if (keys.length > 0) {
    activeTab.value = getTabKey(keys[0]!)
  }
}

/** 获取标签页 key */
function getTabKey(fileName: string): string {
  const base = fileName.substring(fileName.lastIndexOf('/') + 1)
  return base.replace('.jinja2', '')
}

/** 获取标签页标签 */
function getTabLabel(fileName: string): string {
  return getTabKey(fileName)
}

/** 复制代码 */
function copyCode(code: string, fileName: string) {
  navigator.clipboard
    .writeText(code)
    .then(() => {
      message.success('复制成功')
    })
    .catch(() => {
      message.error('复制失败')
    })
}

defineExpose({
  show,
})
</script>
