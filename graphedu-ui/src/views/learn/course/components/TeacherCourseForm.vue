<script setup lang="ts">
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useDebounceFn } from '@vueuse/core'
import type { FormInstance } from 'ant-design-vue'
import { addCourse, checkCourseCodeExists } from '@/api/education/course'
import useUserStore from '@/stores/modules/user'
import DictRadio from '@/components/dict/DictRadio.vue'
import FileUpload from '@/components/FileUpload/index.vue'
import type { CourseCreateDTO } from '@/types/api/education/course.ts'

const { t } = useI18n()
const userStore = useUserStore()

interface Props {
  visible: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  courseCode: '',
  courseName: '',
  faculty: '',
  description: '',
  isPublic: 'Y',
  coverFileId: undefined as number | undefined,
})

// 异步验证课程码唯一性
const validateCourseCodeUnique = useDebounceFn(async (_rule: any, value: string) => {
  if (!value) return Promise.resolve()
  try {
    const res = await checkCourseCodeExists(value)
    if (res.code === 200 && res.data) {
      return Promise.reject(new Error(t('education.course.courseCodeAlreadyExists')))
    }
    return Promise.resolve()
  } catch {
    return Promise.resolve()
  }
}, 500)

const rules = {
  courseCode: [
    {
      required: true,
      message: t('education.course.courseCodeRequired'),
      trigger: 'blur',
    },
    {
      max: 32,
      message: t('education.course.courseCodeLengthInvalid'),
      trigger: 'blur',
    },
    { validator: validateCourseCodeUnique, trigger: 'blur' },
  ],
  courseName: [
    {
      required: true,
      message: t('education.course.courseNameRequired'),
      trigger: 'blur',
    },
    {
      max: 128,
      message: t('education.course.courseNameLengthInvalid'),
      trigger: 'blur',
    },
  ],
}

// 提交
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    // 自动关联当前教师
    const teacherIds: number[] = []
    if (userStore.teacherInfo?.teacherId) {
      teacherIds.push(userStore.teacherInfo.teacherId)
    }

    const data: CourseCreateDTO = {
      courseCode: form.courseCode,
      courseName: form.courseName,
      faculty: form.faculty || undefined,
      description: form.description || undefined,
      isPublic: form.isPublic as 'Y' | 'N',
      coverFileId: form.coverFileId,
      teacherIds,
    }

    const res = await addCourse(data)
    if (res.code === 200) {
      message.success(t('common.addSuccess'))
      emit('success')
      handleCancel()
    }
  } catch (error: any) {
    if (error.errorFields) return
    message.error(t('common.addFailed'))
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  emit('update:visible', false)
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(form, {
    courseCode: '',
    courseName: '',
    faculty: '',
    description: '',
    isPublic: 'Y',
    coverFileId: undefined,
  })
}

// 弹窗关闭时重置
watch(
  () => props.visible,
  (val) => {
    if (!val) {
      resetForm()
    }
  }
)
</script>

<template>
  <a-modal
    :open="visible"
    :title="t('learning.createCourse')"
    :confirm-loading="loading"
    :width="600"
    @cancel="handleCancel"
    @ok="handleSubmit"
  >
    <a-spin :spinning="loading" :tip="t('common.loading')">
      <a-form ref="formRef" :model="form" :rules="rules as any" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item :label="t('education.course.courseCode')" name="courseCode">
          <a-input
            v-model:value="form.courseCode"
            :placeholder="t('education.course.courseCodePlaceholder')"
            :maxlength="32"
          />
        </a-form-item>

        <a-form-item :label="t('education.course.courseName')" name="courseName">
          <a-input
            v-model:value="form.courseName"
            :placeholder="t('education.course.courseNamePlaceholder')"
            :maxlength="128"
          />
        </a-form-item>

        <a-form-item :label="t('common.faculty')" name="faculty">
          <a-input v-model:value="form.faculty" :placeholder="t('common.facultyPlaceholder')" :maxlength="64" />
        </a-form-item>

        <a-form-item :label="t('education.course.description')" name="description">
          <a-textarea
            v-model:value="form.description"
            :placeholder="t('education.course.descriptionPlaceholder')"
            :rows="4"
            :maxlength="500"
            show-count
          />
        </a-form-item>

        <a-form-item :label="t('education.course.isPublic')" name="isPublic">
          <DictRadio v-model:model-value="form.isPublic" dict-type="sys_data_option" />
        </a-form-item>

        <a-form-item :label="t('education.course.coverImage')" name="coverFileId">
          <FileUpload
            v-model="form.coverFileId"
            :file-category="2"
            accept=".jpg,.jpeg,.png,.gif,.webp"
            access-level="2"
            download-flag="0"
          />
        </a-form-item>
      </a-form>
    </a-spin>
  </a-modal>
</template>
