<script setup lang="ts">
import { downloadFile, getFileInfo } from '@/api/system/upload.ts'
import type { FileInfoVO } from '@/types/api/system/upload.ts'
import { DownloadOutlined, FileOutlined, CloudDownloadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

/**
 * 二进制资源面板
 * 在 ChapterResource.vue 的 Golden Layout 中展示二进制类型资源（可执行文件、压缩包等）
 *
 * 组件功能：
 * - 显示文件信息卡片（名称、大小、上传/更新信息等）
 * - 显示 description 字段
 * - 提供下载功能
 */
const props = defineProps<{
  /** 资料 ID */
  resourceId: number
  /** 资料名称（Tab 标题，供调试用） */
  resourceName?: string
  /** 文件 ID（由后端 fileId 字段提供，优先使用） */
  fileId?: number
  /** 文件 URL（由后端 fileUrl 字段提供，降级使用） */
  fileUrl?: string
  /** 描述信息 */
  description?: string
  /** Golden Layout 注入的 refId（内部使用）*/
  refId?: number
}>()

// 文件信息
const fileInfo = ref<FileInfoVO | null>(null)
const isLoading = ref(false)
const isDownloading = ref(false)
const hasError = ref(false)

/**
 * 格式化文件大小
 */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
}

/**
 * 格式化时间
 */
function formatTime(timeStr?: string): string {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * 获取文件扩展名图标类型
 */
function getFileIconType(): string {
  const name = props.resourceName || ''
  const ext = name.match(/\.(\w+)$/i)?.[1]?.toLowerCase() || ''

  // 压缩包类型
  if (['zip', 'rar', '7z', 'tar', 'gz', 'bz2'].includes(ext)) {
    return 'compress'
  }
  // 可执行文件类型
  if (['exe', 'msi', 'app', 'dmg', 'deb', 'rpm'].includes(ext)) {
    return 'executable'
  }
  // 代码/脚本类型
  if (['py', 'js', 'ts', 'java', 'cpp', 'c', 'sh', 'bat', 'ps1'].includes(ext)) {
    return 'code'
  }
  return 'default'
}

/**
 * 获取文件类型描述
 */
function getFileTypeDescription(): string {
  const type = getFileIconType()
  const typeMap: Record<string, string> = {
    compress: '压缩文件',
    executable: '可执行文件',
    code: '代码文件',
    default: '二进制文件',
  }
  return typeMap[type] ?? typeMap.default ?? '二进制文件'
}

/**
 * 加载文件详细信息
 */
async function loadFileInfo() {
  if (!props.fileId) return

  isLoading.value = true
  try {
    const res = await getFileInfo(props.fileId)
    if (res.code === 200 && res.data) {
      fileInfo.value = res.data
    } else {
      hasError.value = true
    }
  } catch (e) {
    console.error('[ChapterBinaryPanel] 加载文件信息失败', e)
    hasError.value = true
  } finally {
    isLoading.value = false
  }
}

/**
 * 下载文件
 */
async function handleDownload() {
  // 优先使用 fileUrl 直接下载（避免后端转发）
  const downloadUrl = props.fileUrl
  if (downloadUrl) {
    window.open(downloadUrl, '_blank')
    return
  }

  // 降级：通过后端代理下载
  if (!props.fileId) {
    message.error('无法下载：缺少文件信息')
    return
  }

  isDownloading.value = true
  try {
    const res = await downloadFile(props.fileId)
    if (res.code === 200 && res.data) {
      // 创建临时下载链接
      const link = document.createElement('a')
      link.href = res.data.fileUrl
      link.download = props.resourceName || fileInfo.value?.fileName || 'download'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      message.success('下载已开始')
    } else {
      message.error('下载失败')
    }
  } catch (e) {
    console.error('[ChapterBinaryPanel] 下载文件失败', e)
    message.error('下载失败，请稍后重试')
  } finally {
    isDownloading.value = false
  }
}

onMounted(() => {
  loadFileInfo()
})
</script>

<template>
  <div class="chapter-binary-panel h-full w-full overflow-auto">
    <div class="binary-content max-w-3xl mx-auto p-6">
      <!-- 文件信息卡片 -->
      <a-card class="file-card mb-4" :bordered="false" :loading="isLoading">
        <template #title>
          <div class="flex items-center gap-2">
            <FileOutlined class="text-lg" />
            <span class="font-medium">文件信息</span>
          </div>
        </template>

        <!-- 错误状态 -->
        <a-result v-if="hasError" status="error" title="文件信息加载失败" sub-title="该资源可能已被删除或无法访问" />

        <!-- 文件信息内容 -->
        <div v-else class="file-info-content">
          <!-- 文件名称 -->
          <div class="info-item">
            <span class="info-label">文件名称</span>
            <span class="info-value">{{ props.resourceName || '-' }}</span>
          </div>

          <!-- 文件类型 -->
          <div class="info-item">
            <span class="info-label">文件类型</span>
            <a-tag color="blue">{{ getFileTypeDescription() }}</a-tag>
          </div>

          <!-- 文件大小 -->
          <div v-if="fileInfo" class="info-item">
            <span class="info-label">文件大小</span>
            <span class="info-value">{{ formatFileSize(fileInfo.fileSize) }}</span>
          </div>

          <!-- 上传时间 -->
          <div v-if="fileInfo" class="info-item">
            <span class="info-label">上传时间</span>
            <span class="info-value text-gray-600 dark:text-gray-400">{{ formatTime(fileInfo.createTime) }}</span>
          </div>

          <!-- 更新时间 -->
          <div v-if="fileInfo && fileInfo.updateTime" class="info-item">
            <span class="info-label">更新时间</span>
            <span class="info-value text-gray-600 dark:text-gray-400">{{ formatTime(fileInfo.updateTime) }}</span>
          </div>

          <!-- 下载次数 -->
          <div v-if="fileInfo" class="info-item">
            <span class="info-label">下载次数</span>
            <span class="info-value">{{ fileInfo.downloadCount }} 次</span>
          </div>
        </div>

        <!-- 下载按钮 -->
        <template #actions>
          <a-button type="primary" size="large" :loading="isDownloading" @click="handleDownload" class="download-btn">
            <template #icon>
              <DownloadOutlined v-if="!isDownloading" />
            </template>
            {{ isDownloading ? '下载中...' : '下载文件' }}
          </a-button>
        </template>
      </a-card>

      <!-- 描述信息卡片 -->
      <a-card v-if="props.description" class="description-card" :bordered="false">
        <template #title>
          <div class="flex items-center gap-2">
            <CloudDownloadOutlined class="text-lg" />
            <span class="font-medium">资源说明</span>
          </div>
        </template>

        <div class="description-content whitespace-pre-wrap text-gray-700 dark:text-gray-300">
          {{ props.description }}
        </div>
      </a-card>

      <!-- 无 fileId 且无 fileUrl 的提示 -->
      <a-result
        v-if="!props.fileId && !props.fileUrl"
        status="warning"
        title="无法加载文件"
        sub-title="该资料尚未上传文件或文件链接无效"
        class="mt-8"
      />
    </div>
  </div>
</template>

<style scoped>
@reference "#main.css";

.chapter-binary-panel {
  background: var(--ge-bg-container);
}

.binary-content {
  padding: 24px;
}

.file-card {
  @apply rounded-lg shadow-sm;
}

.description-card {
  @apply rounded-lg shadow-sm;
}

.info-item {
  @apply flex justify-between items-center py-3 border-b;
  border-color: var(--ge-border-color);
}

.info-item:last-child {
  @apply border-b-0;
}

.info-label {
  @apply text-sm font-medium;
  color: var(--ge-text-secondary);
}

.info-value {
  @apply text-sm font-medium;
  color: var(--ge-text-primary);
}

.download-btn {
  @apply w-full;
}

.description-content {
  @apply text-sm leading-relaxed;
}
</style>
