<template>
  <a-drawer :open="visible" title="文本化操作" :width="520" placement="right" @close="handleClose">
    <a-space direction="vertical" style="width: 100%" :size="16">
      <a-descriptions :column="1" size="small" bordered>
        <a-descriptions-item label="资源名称">{{ resource?.resourceName || '-' }}</a-descriptions-item>
        <a-descriptions-item label="资源类型">{{ resource?.resourceType || '-' }}</a-descriptions-item>
        <a-descriptions-item label="处理状态">
          <DictTag :options="text_processing_status" :value="statusInfo.parseStatus" />
        </a-descriptions-item>
      </a-descriptions>

      <a-card size="small" title="任务参数">
        <a-form layout="vertical">
          <a-form-item label="处理模式">
            <a-select v-model:value="parseMode" :disabled="processing">
              <a-select-option value="default">默认</a-select-option>
            </a-select>
          </a-form-item>
        </a-form>
      </a-card>

      <a-card size="small" title="任务进度">
        <a-progress :percent="progressPercent" :status="progressStatus" />
        <a-space>
          <a-button type="primary" :loading="submitting" :disabled="processing" @click="submitTask">执行</a-button>
          <a-button :loading="polling" @click="refreshStatus">刷新状态</a-button>
        </a-space>
      </a-card>

      <a-card size="small" title="结果文档">
        <a-descriptions :column="1" size="small">
          <a-descriptions-item label="文本文件ID">{{ statusInfo.textFileId ?? '-' }}</a-descriptions-item>
          <a-descriptions-item label="页数">{{ statusInfo.pageCount ?? '-' }}</a-descriptions-item>
          <a-descriptions-item label="Markdown 长度">{{ statusInfo.markdownLength ?? '-' }}</a-descriptions-item>
          <a-descriptions-item label="存储Key">{{ statusInfo.markdownS3Key || '-' }}</a-descriptions-item>
        </a-descriptions>
        <a-space v-if="statusInfo.markdownUrl" style="margin-top: 8px">
          <a :href="statusInfo.markdownUrl" target="_blank" rel="noopener">打开结果文档</a>
        </a-space>
      </a-card>

      <a-alert v-if="statusInfo.errorMessage" type="error" show-icon :message="statusInfo.errorMessage" />
    </a-space>
  </a-drawer>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import DictTag from '@/components/dict/DictTag.vue'
import { useDict } from '@/utils/dict.ts'
import { submitParse, getParseStatus } from '@/api/education/chapterResource.ts'
import { ProcessStatus } from '@/constants/process'
import type { ChapterResourceListVO } from '@/types/api/education/chapterResource.ts'

interface Props {
  visible: boolean
  resource?: ChapterResourceListVO
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

interface ParseStatusPayload {
  parseStatus: string
  pageCount?: number
  markdownLength?: number
  textFileId?: number
  mineruTaskId?: string
  markdownS3Key?: string
  markdownUrl?: string
  errorMessage?: string
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { text_processing_status } = useDict('text_processing_status')
const parseMode = ref('default')
const submitting = ref(false)
const polling = ref(false)
const pollTimer = ref<number | null>(null)

const statusInfo = ref<ParseStatusPayload>({
  parseStatus: '0',
})

const processing = computed(() => statusInfo.value.parseStatus === ProcessStatus.RUNNING)
const progressPercent = computed(() => {
  if (statusInfo.value.parseStatus === '1') return 60
  if (statusInfo.value.parseStatus === '2' || statusInfo.value.parseStatus === '3') return 100
  return 0
})
const progressStatus = computed(() => {
  if (statusInfo.value.parseStatus === '3') return 'exception'
  if (statusInfo.value.parseStatus === '2') return 'success'
  if (statusInfo.value.parseStatus === '1') return 'active'
  return 'normal'
})

const clearPollTimer = () => {
  if (pollTimer.value !== null) {
    window.clearInterval(pollTimer.value)
    pollTimer.value = null
  }
}

const refreshStatus = async () => {
  if (!props.resource?.resourceId) return
  polling.value = true
  try {
    const res = await getParseStatus(props.resource.resourceId)
    if (res.code === 200 && res.data) {
      statusInfo.value = {
        parseStatus: res.data.parseStatus || '0',
        pageCount: res.data.pageCount,
        markdownLength: res.data.markdownLength,
        textFileId: res.data.textFileId,
        mineruTaskId: res.data.mineruTaskId,
        markdownS3Key: res.data.markdownS3Key,
        markdownUrl: res.data.markdownUrl,
        errorMessage: res.data.errorMessage,
      }
      if (statusInfo.value.parseStatus !== ProcessStatus.RUNNING) {
        clearPollTimer()
      }
    }
  } catch (_e) {
    message.error('获取文本化状态失败')
  } finally {
    polling.value = false
  }
}

const startPolling = () => {
  clearPollTimer()
  pollTimer.value = window.setInterval(() => {
    refreshStatus()
  }, 3000)
}

const submitTask = async () => {
  if (!props.resource?.resourceId) return
  submitting.value = true
  try {
    const res = await submitParse(props.resource.resourceId)
    if (res.code === 200) {
      message.success('任务已提交')
      statusInfo.value.parseStatus = res.data?.parseStatus || ProcessStatus.RUNNING
      startPolling()
      emit('success')
      await refreshStatus()
    }
  } catch (_e) {
    message.error('提交文本化任务失败')
  } finally {
    submitting.value = false
  }
}

const resetState = () => {
  parseMode.value = 'default'
  statusInfo.value = {
    parseStatus: '0',
  }
}

const handleClose = () => {
  clearPollTimer()
  emit('update:visible', false)
}

watch(
  () => props.visible,
  async (visible) => {
    if (visible) {
      await refreshStatus()
      if (statusInfo.value.parseStatus === ProcessStatus.RUNNING) {
        startPolling()
      }
    } else {
      clearPollTimer()
      resetState()
    }
  }
)

watch(
  () => props.resource?.resourceId,
  async () => {
    if (props.visible) {
      await refreshStatus()
    }
  }
)

onBeforeUnmount(() => {
  clearPollTimer()
})
</script>
