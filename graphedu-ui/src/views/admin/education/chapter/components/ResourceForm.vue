<template>
  <a-modal
    :visible="visible"
    :title="isEdit ? '编辑资源' : '添加资源'"
    :width="600"
    :confirm-loading="loading"
    @ok="handleSubmit"
    @cancel="handleCancel"
  >
    <a-form :model="form" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
      <a-form-item label="资源名称" required>
        <a-input v-model:value="form.resourceName" placeholder="请输入资源名称" />
      </a-form-item>
      <a-form-item label="资源类型" required>
        <a-select v-model:value="form.resourceType" placeholder="请选择资源类型">
          <a-select-option value="video">视频</a-select-option>
          <a-select-option value="document">文档(PDF/Office)</a-select-option>
          <a-select-option value="text">文本</a-select-option>
          <a-select-option value="image">图片</a-select-option>
          <a-select-option value="audio">音频</a-select-option>
          <a-select-option value="archive">压缩包</a-select-option>
          <a-select-option value="binary">二进制文件</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="上传文件">
        <FileUpload
          v-model="form.fileId"
          :accept="getFileAccept()"
          :file-category="7"
          access-level="1"
          download-flag="1"
        />
      </a-form-item>
      <a-form-item label="可见性">
        <a-radio-group v-model:value="form.isVisible">
          <a-radio value="Y">可见</a-radio>
          <a-radio value="N">隐藏</a-radio>
        </a-radio-group>
      </a-form-item>
      <a-form-item label="状态">
        <a-radio-group v-model:value="form.status">
          <a-radio value="0">正常</a-radio>
          <a-radio value="1">停用</a-radio>
        </a-radio-group>
      </a-form-item>
      <a-form-item label="显示顺序">
        <a-input-number v-model:value="form.displayOrder" :min="0" style="width: 100%" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { addChapterResource, updateChapterResource } from '@/api/education/chapter.ts'
import FileUpload from '@/components/FileUpload/index.vue'

interface Props {
  visible: boolean
  chapterId: number
  resource?: any
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const loading = ref(false)
const form = ref({
  resourceName: '',
  resourceType: 'document',
  fileId: undefined as number | null | undefined,
  isVisible: 'Y',
  status: '0',
  displayOrder: 0,
})

// 根据资源类型获取接受的文件格式
const getFileAccept = () => {
  const map: Record<string, string> = {
    video: '.mp4,.avi,.mkv,.mov,.wmv',
    document: '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx',
    text: '.txt,.md',
    image: '.jpg,.jpeg,.png,.gif,.webp',
    audio: '.mp3,.wav,.flac,.aac',
    archive: '.zip,.rar,.7z,.tar,.gz',
    binary: '.exe,.msi,.apk,.dmg,.iso,.bin',
  }
  return map[form.value.resourceType] || '*'
}

const isEdit = computed(() => !!props.resource)

// 监听 resource 变化，填充表单
watch(
  () => props.resource,
  (newResource) => {
    if (newResource) {
      form.value = {
        resourceName: newResource.resourceName || '',
        resourceType: newResource.resourceType || 'document',
        fileId: newResource.fileId ?? null,
        isVisible: newResource.isVisible || 'Y',
        status: newResource.status || '0',
        displayOrder: newResource.displayOrder || 0,
      }
    } else {
      form.value = {
        resourceName: '',
        resourceType: 'document',
        fileId: null,
        isVisible: 'Y',
        status: '0',
        displayOrder: 0,
      }
    }
  },
  { immediate: true }
)

// 提交表单
const handleSubmit = async () => {
  if (!form.value.resourceName) {
    message.warning('请输入资源名称')
    return
  }

  loading.value = true
  try {
    // 构建提交数据，fileId 为 null 时不传
    const submitData = {
      resourceName: form.value.resourceName,
      resourceType: form.value.resourceType,
      fileId: form.value.fileId ?? undefined,
      isVisible: form.value.isVisible,
      status: form.value.status,
      displayOrder: form.value.displayOrder,
    }

    if (isEdit.value) {
      const res = await updateChapterResource(props.chapterId, props.resource.resourceId, submitData as any)
      if (res.code === 200) {
        message.success('更新成功')
        emit('success')
        emit('update:visible', false)
      }
    } else {
      const res = await addChapterResource(props.chapterId, submitData as any)
      if (res.code === 200) {
        message.success('添加成功')
        emit('success')
        emit('update:visible', false)
      }
    }
  } catch (_e) {
    message.error(isEdit.value ? '更新失败' : '添加失败')
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  emit('update:visible', false)
}
</script>

<style scoped>
:deep(.ant-form-item) {
  margin-bottom: 16px;
}
</style>
