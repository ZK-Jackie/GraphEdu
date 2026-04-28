<template>
  <div class="user-avatar">
    <a-avatar :size="120" :src="avatarUrl">
      <template #icon>
        <UserOutlined />
      </template>
    </a-avatar>
    <div class="avatar-actions">
      <a-upload :before-upload="beforeUpload" :show-upload-list="false" accept="image/*">
        <a-button type="primary" size="small" :loading="uploading">
          <template #icon><UploadOutlined /></template>
          上传头像
        </a-button>
      </a-upload>
    </div>
    <div class="avatar-tips">
      <a-typography-text type="secondary"> 只能上传 JPG/PNG 格式图片，建议大小不超过 2MB </a-typography-text>
    </div>

    <!-- 图片裁剪弹窗 -->
    <a-modal v-model:open="cropVisible" title="裁剪头像" :width="600" @ok="handleCropConfirm">
      <div class="crop-container">
        <img ref="cropImage" :src="cropImageUrl" style="max-width: 100%" />
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { UserOutlined, UploadOutlined } from '@ant-design/icons-vue'
import { updateUserAvatar } from '@/api/system/user'
import { uploadAvatar } from '@/api/system/upload'

interface Props {
  avatarFileId?: number
  avatarPath?: string
  userName?: string
}

interface Emits {
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const cropVisible = ref(false)
const cropImageUrl = ref('')
const cropImage = ref<HTMLImageElement>()
const uploading = ref(false)
const uploadedFilePath = ref('')

// 头像 URL
const avatarUrl = computed(() => {
  // 优先使用上传后的文件路径
  if (uploadedFilePath.value) {
    return uploadedFilePath.value
  }
  // 其次使用传入的头像路径
  if (props.avatarPath) {
    return props.avatarPath
  }
  // 如果都没有，返回 undefined 显示默认图标
  return undefined
})

// 上传前校验
const beforeUpload = (file: File) => {
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    message.error('只能上传图片文件')
    return false
  }

  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isLt2M) {
    message.error('图片大小不能超过 2MB')
    return false
  }

  // 读取图片并显示裁剪弹窗
  const reader = new FileReader()
  reader.onload = (e) => {
    cropImageUrl.value = e.target?.result as string
    cropVisible.value = true
  }
  reader.readAsDataURL(file)

  return false
}

// 确认裁剪并上传
const handleCropConfirm = async () => {
  try {
    uploading.value = true

    // 将 base64 转换为 Blob
    const res = await fetch(cropImageUrl.value)
    const blob = await res.blob()
    const file = new File([blob], 'avatar.jpg', { type: 'image/jpeg' })

    // 上传头像
    const uploadRes = await uploadAvatar(file)
    if (uploadRes.code === 200 && uploadRes.data) {
      // 更新用户头像
      const updateRes = await updateUserAvatar(uploadRes.data.fileId)
      if (updateRes.code === 200) {
        message.success('头像上传成功')
        uploadedFilePath.value = uploadRes.data.filePath
        cropVisible.value = false
        emit('success')
      }
    }
  } catch (error: any) {
    console.error('头像上传失败:', error)
    message.error(error.message || '头像上传失败')
  } finally {
    uploading.value = false
  }
}

// 监听 avatarFileId 变化，重置上传的文件路径
watch(
  () => props.avatarFileId,
  () => {
    uploadedFilePath.value = ''
  }
)
</script>

<style scoped>
.user-avatar {
  text-align: center;

  .avatar-actions {
    margin-top: 16px;
  }

  .avatar-tips {
    margin-top: 8px;
  }

  .crop-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 300px;
  }
}
</style>
