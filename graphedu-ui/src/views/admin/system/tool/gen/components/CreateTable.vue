<template>
  <a-modal v-model:open="visible" title="创建表" width="800px" :destroy-on-close="true">
    <div style="margin-bottom: 8px">创建表语句（支持多个建表语句）：</div>
    <a-textarea v-model:value="content" :rows="10" placeholder="请输入建表 SQL 语句" />

    <template #footer>
      <a-button type="primary" @click="handleCreateTable">确定</a-button>
      <a-button @click="visible = false">取消</a-button>
    </template>
  </a-modal>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import { createTable } from '@/api/system/tool/gen'

const emit = defineEmits<{
  ok: []
}>()

const visible = ref(false)
const content = ref('')

/** 显示弹窗 */
function show() {
  visible.value = true
}

/** 创建按钮操作 */
function handleCreateTable() {
  if (!content.value.trim()) {
    message.warning('请输入建表语句')
    return
  }
  createTable({ sql: content.value })
    .then((res) => {
      message.success(res.msg || '创建成功')
      if (res.code === 200) {
        visible.value = false
        content.value = ''
        emit('ok')
      }
    })
    .catch(() => {})
}

defineExpose({
  show,
})
</script>
