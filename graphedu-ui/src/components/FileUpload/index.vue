<template>
  <div class="file-upload-wrap">
    <!-- 上传区域 -->
    <a-upload-dragger
      v-if="!fileInfo"
      :accept="accept"
      :multiple="false"
      :show-upload-list="false"
      :before-upload="handleBeforeUpload"
      :custom-request="handleCustomRequest"
      :disabled="disabled"
      class="file-upload-dragger"
      :class="{ 'file-upload-dragger--uploading': uploading }"
    >
      <div class="file-upload-inner">
        <template v-if="uploading">
          <a-spin :spinning="true" />
          <p class="file-upload-hint">上传中，请稍候...</p>
          <a-progress :percent="uploadPercent" class="file-upload-progress" />
        </template>
        <template v-else>
          <div class="file-upload-icon">
            <inbox-outlined />
          </div>
          <p class="file-upload-text">点击或拖拽文件到此区域上传</p>
          <p class="file-upload-hint">
            <template v-if="accept">支持格式：{{ accept }}</template>
            <template v-if="maxSize">，大小限制：{{ formatSize(maxSize) }}</template>
          </p>
        </template>
      </div>
    </a-upload-dragger>

    <!-- 已上传文件展示 -->
    <div v-else class="file-upload-success">
      <div class="file-info">
        <div class="file-info-icon">
          <file-outlined />
        </div>
        <div class="file-info-content">
          <div class="file-info-name" :title="fileInfo.fileName">{{ fileInfo.fileName }}</div>
          <div class="file-info-meta">{{ formatSize(fileInfo.fileSize) }}</div>
        </div>
        <div v-if="!disabled" class="file-info-actions">
          <a-tooltip title="重新上传">
            <a-button type="text" size="small" @click="handleReupload">
              <template #icon>
                <sync-outlined />
              </template>
            </a-button>
          </a-tooltip>
          <a-tooltip title="删除">
            <a-button type="text" size="small" danger @click="handleRemove">
              <template #icon>
                <delete-outlined />
              </template>
            </a-button>
          </a-tooltip>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { InboxOutlined, FileOutlined, SyncOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { uploadFile, getFileInfo } from '@/api/system/upload.ts'
import type { FileInfoVO, UploadFileDTO } from '@/types/api/system/upload.ts'

interface Props {
  /** 已上传的文件ID（v-model） */
  modelValue?: number | null
  /** 允许的文件类型，如 '.pdf,.docx' */
  accept?: string
  /** 文件分类: 1-头像 2-课程封面 3-书籍封面 4-书籍文件 5-笔记附件 6-作业 7-课件 */
  fileCategory?: number
  /** 最大文件大小（字节） */
  maxSize?: number
  /** 访问级别: 0-私有 1-登录用户 2-公开 */
  accessLevel?: string
  /** 是否允许下载: 0-否 1-是 */
  downloadFlag?: string
  /** 是否禁用 */
  disabled?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: number | null): void
  (e: 'uploaded', fileInfo: FileInfoVO): void
  (e: 'removed'): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  accept: undefined,
  fileCategory: 7,
  maxSize: 100 * 1024 * 1024, // 100MB
  accessLevel: '1',
  downloadFlag: '1',
  disabled: false,
})

const emit = defineEmits<Emits>()

// 上传状态
const uploading = ref(false)
const uploadPercent = ref(0)

// 已上传的文件信息
const fileInfo = ref<FileInfoVO | null>(null)

// 监听 modelValue 变化，加载文件信息
watch(
  () => props.modelValue,
  async (newVal) => {
    if (newVal) {
      await loadFileInfo(newVal)
    } else {
      fileInfo.value = null
    }
  },
  { immediate: true }
)

/**
 * 加载文件信息
 */
async function loadFileInfo(fileId: number) {
  try {
    const { data } = await getFileInfo(fileId)
    if (data) {
      fileInfo.value = data
    }
  } catch (err) {
    console.error('[FileUpload] 加载文件信息失败:', err)
    fileInfo.value = null
  }
}

/**
 * 上传前校验
 */
function handleBeforeUpload(file: File): boolean {
  // 文件大小校验
  if (props.maxSize && file.size > props.maxSize) {
    message.error(`文件大小超过限制（${formatSize(props.maxSize)}）`)
    return false
  }

  // 文件类型校验
  if (props.accept) {
    const ext = `.${file.name.split('.').pop()?.toLowerCase()}`
    const acceptList = props.accept.split(',').map((s) => s.trim().toLowerCase())
    if (!acceptList.includes(ext) && !acceptList.includes(file.type)) {
      message.error(`不支持的文件类型，仅允许：${props.accept}`)
      return false
    }
  }

  return true
}

/**
 * 自定义上传逻辑（带进度条）
 */
async function handleCustomRequest(options: any) {
  const { file } = options

  uploading.value = true
  uploadPercent.value = 0

  // 模拟进度（真实进度需要 XMLHttpRequest，此处用时间模拟）
  const progressInterval = setInterval(() => {
    if (uploadPercent.value < 90) {
      uploadPercent.value += 10
    }
  }, 200)

  try {
    const uploadDTO: UploadFileDTO = {
      fileCategory: props.fileCategory,
      accessLevel: props.accessLevel,
      downloadFlag: props.downloadFlag,
    }

    const { data } = await uploadFile(file, uploadDTO)

    clearInterval(progressInterval)
    uploadPercent.value = 100

    if (data) {
      fileInfo.value = data
      emit('update:modelValue', data.fileId)
      emit('uploaded', data)
      message.success(`${file.name} 上传成功`)
    }
  } catch (err: any) {
    clearInterval(progressInterval)
    message.error(`${file.name} 上传失败: ${err?.message || '未知错误'}`)
    options.onError(err)
  } finally {
    uploading.value = false
    uploadPercent.value = 0
  }
}

/**
 * 重新上传（清除当前文件，显示上传区域）
 */
function handleReupload() {
  fileInfo.value = null
  emit('update:modelValue', null)
  emit('removed')
}

/**
 * 移除文件
 */
function handleRemove() {
  fileInfo.value = null
  emit('update:modelValue', null)
  emit('removed')
}

/**
 * 格式化文件大小
 */
function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}
</script>

<style scoped>
@reference "#main.css";

.file-upload-wrap {
  @apply w-full;
}

.file-upload-dragger {
  @apply w-full;
}

.file-upload-dragger--uploading {
  @apply cursor-not-allowed opacity-80;
}

.file-upload-inner {
  @apply flex flex-col items-center justify-center py-8 gap-2;
}

.file-upload-icon {
  @apply text-4xl text-blue-400;
}

.file-upload-text {
  @apply text-base text-gray-700 m-0;
}

.file-upload-hint {
  @apply text-sm text-gray-400 m-0;
}

.file-upload-progress {
  @apply w-3/4 mt-2;
}

.file-upload-success {
  @apply border border-gray-200 rounded-lg p-3 bg-gray-50;
}

.file-info {
  @apply flex items-center gap-3;
}

.file-info-icon {
  @apply text-2xl text-blue-500 flex-shrink-0;
}

.file-info-content {
  @apply flex-1 overflow-hidden;
}

.file-info-name {
  @apply text-sm font-medium text-gray-800 truncate;
}

.file-info-meta {
  @apply text-xs text-gray-400 mt-0.5;
}

.file-info-actions {
  @apply flex items-center gap-1 flex-shrink-0;
}
</style>
