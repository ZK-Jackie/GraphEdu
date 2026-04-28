<script setup lang="ts">
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useDebounceFn } from '@vueuse/core'
import type { FormInstance } from 'ant-design-vue'
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons-vue'
import { checkCourseCodeExists, getCourseList } from '@/api/education/course'
import { joinCourse } from '@/api/education/student_course'

const { t } = useI18n()

interface Props {
  visible: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success', courseId: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const loading = ref(false)
const courseCode = ref('')
const codeStatus = ref<'idle' | 'checking' | 'valid' | 'invalid'>('idle')

// 防抖验证课程码是否存在
const validateCourseCode = useDebounceFn(async (value: string) => {
  if (!value || value.trim().length === 0) {
    codeStatus.value = 'idle'
    return
  }

  codeStatus.value = 'checking'
  try {
    const res = await checkCourseCodeExists(value.trim())
    if (res.code === 200) {
      codeStatus.value = res.data ? 'valid' : 'invalid'
    } else {
      codeStatus.value = 'idle'
    }
  } catch {
    codeStatus.value = 'idle'
  }
}, 500)

// 监听输入变化
watch(courseCode, (val) => {
  validateCourseCode(val)
})

// 提交
const handleSubmit = async () => {
  const code = courseCode.value?.trim()
  if (!code) {
    message.warning(t('learning.joinByCodePlaceholder'))
    return
  }

  if (codeStatus.value === 'invalid') {
    message.error(t('learning.joinByCodeNotFound'))
    return
  }

  loading.value = true
  try {
    // 先查询课程获取 courseId
    const listRes = await getCourseList({
      courseCode: code,
      page: 1,
      size: 1,
    } as any)
    if (listRes.code !== 200 || !listRes.data.rows?.length) {
      message.error(t('learning.joinByCodeNotFound'))
      return
    }

    const courseId = listRes.data.rows[0]!.courseId
    const joinRes = await joinCourse({ courseId })
    if (joinRes.code === 200) {
      message.success(t('learning.joinByCodeSuccess'))
      emit('success', courseId)
      handleCancel()
    } else {
      message.error(joinRes.msg || t('learning.joinByCodeFailed'))
    }
  } catch (error: any) {
    const msg = error?.response?.data?.msg
    if (msg?.includes('已加入') || msg?.includes('already')) {
      message.warning(t('learning.joinByCodeAlreadyJoined'))
    } else {
      message.error(msg || t('learning.joinByCodeFailed'))
    }
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  emit('update:visible', false)
}

// 弹窗关闭时重置
watch(
  () => props.visible,
  (val) => {
    if (!val) {
      courseCode.value = ''
      codeStatus.value = 'idle'
    }
  }
)
</script>

<template>
  <a-modal
    :open="visible"
    :title="t('learning.joinByCodeDialogTitle')"
    :confirm-loading="loading"
    :width="420"
    @cancel="handleCancel"
    @ok="handleSubmit"
  >
    <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
      <a-form-item :label="t('education.course.courseCode')">
        <a-input
          v-model:value="courseCode"
          :placeholder="t('learning.joinByCodePlaceholder')"
          :maxlength="50"
          allow-clear
          @press-enter="handleSubmit"
        >
          <template #suffix>
            <CheckCircleOutlined v-if="codeStatus === 'valid'" style="color: #52c41a" />
            <CloseCircleOutlined v-else-if="codeStatus === 'invalid'" style="color: #ff4d4f" />
            <a-spin v-else-if="codeStatus === 'checking'" size="small" />
          </template>
        </a-input>
        <div v-if="codeStatus === 'invalid'" class="text-red-500 text-xs mt-1">
          {{ t('learning.joinByCodeNotFound') }}
        </div>
      </a-form-item>
    </a-form>
  </a-modal>
</template>
