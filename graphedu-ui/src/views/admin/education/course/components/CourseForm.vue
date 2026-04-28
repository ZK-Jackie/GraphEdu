<template>
  <a-modal
    :open="visible"
    :title="title"
    :confirm-loading="loading"
    :width="600"
    @cancel="handleCancel"
    @ok="handleSubmit"
  >
    <a-spin :spinning="loading" :tip="t('common.loading')">
      <a-form ref="formRef" :model="form" :rules="rules as any" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-row>
          <a-col :span="24">
            <a-form-item :label="t('education.course.courseCode')" name="courseCode">
              <a-input
                v-model:value="form.courseCode"
                :placeholder="t('education.course.courseCodePlaceholder')"
                :maxlength="32"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row>
          <a-col :span="24">
            <a-form-item :label="t('education.course.courseName')" name="courseName">
              <a-input
                v-model:value="form.courseName"
                :placeholder="t('education.course.courseNamePlaceholder')"
                :maxlength="128"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row>
          <a-col :span="24">
            <a-form-item :label="t('common.faculty')" name="faculty">
              <a-input v-model:value="form.faculty" :placeholder="t('common.facultyPlaceholder')" :maxlength="64" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row>
          <a-col :span="24">
            <a-form-item :label="t('education.course.description')" name="description">
              <a-textarea
                v-model:value="form.description"
                :placeholder="t('education.course.descriptionPlaceholder')"
                :rows="4"
                :maxlength="500"
                show-count
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row>
          <a-col :span="24">
            <a-form-item :label="t('education.course.isPublic')" name="isPublic">
              <DictRadio v-model:model-value="form.isPublic" dict-type="sys_data_option" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row>
          <a-col :span="24">
            <a-form-item :label="t('education.course.teachers')" name="teacherIds">
              <a-select
                v-model:value="form.teacherIds"
                mode="multiple"
                :placeholder="t('education.course.teachersPlaceholder')"
                :options="teacherOptions"
                :field-names="{ label: 'realName', value: 'teacherId' }"
                :filter-option="
                  (input, option) =>
                    (option?.realName ?? '').toLowerCase().includes(input.toLowerCase()) ||
                    (option?.teacherNo ?? '').toLowerCase().includes(input.toLowerCase())
                "
                allow-clear
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row>
          <a-col :span="24">
            <a-form-item :label="t('education.course.coverImage')" name="coverFileId">
              <FileUpload
                v-model="form.coverFileId"
                :file-category="2"
                accept=".jpg,.jpeg,.png,.gif,.webp"
                access-level="2"
                download-flag="0"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <template v-if="!isEdit">
          <a-row>
            <a-col :span="24">
              <a-form-item :label="t('common.status')" name="status">
                <DictRadio v-model:model-value="form.status" dict-type="sys_data_status" />
              </a-form-item>
            </a-col>
          </a-row>
        </template>
      </a-form>
    </a-spin>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useDebounceFn } from '@vueuse/core'
import type { FormInstance } from 'ant-design-vue'
import { addCourse, updateCourse, getCourseDetail, checkCourseCodeExists } from '@/api/education/course.ts'
import { getTeacherList } from '@/api/education/teacher.ts'
import DictRadio from '../../../../../components/dict/DictRadio.vue'
import FileUpload from '@/components/FileUpload/index.vue'
import type { CourseCreateDTO, CourseUpdateDTO } from '@/types/api/education/course.ts'
import type { TeacherListVO } from '@/types/api/education/teacher.ts'

const { t } = useI18n()

interface Props {
  visible: boolean
  courseId?: number
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const loading = ref(false)

// 是否编辑模式
const isEdit = computed(() => !!props.courseId)

// 弹窗标题
const title = computed(() => (isEdit.value ? t('education.course.editCourse') : t('education.course.addCourse')))

// 表单数据
const form = reactive<Partial<CourseCreateDTO & CourseUpdateDTO> & { teacherIds?: number[] }>({
  courseCode: '',
  courseName: '',
  faculty: '',
  description: '',
  isPublic: 'Y',
  coverFileId: undefined,
  status: '0',
  teacherIds: [],
})

// 教师选项
const teacherOptions = ref<TeacherListVO[]>([])

// 加载选项
const loadOptions = async () => {
  try {
    const teacherRes = await getTeacherList({ page: 1, size: 100 })
    if (teacherRes.code === 200) teacherOptions.value = teacherRes.data.rows
  } catch (error) {
    console.error('加载选项失败:', error)
  }
}

// 异步验证课程代码唯一性（防抖 500ms）
const validateCourseCodeUnique = useDebounceFn(async (_rule: any, value: string) => {
  if (!value) {
    return Promise.resolve()
  }

  try {
    const excludeCourseId = isEdit.value ? props.courseId : undefined
    const res = await checkCourseCodeExists(value, excludeCourseId)
    if (res.code === 200 && res.data) {
      return Promise.reject(new Error(t('education.course.courseCodeAlreadyExists')))
    }
    return Promise.resolve()
  } catch (error) {
    return Promise.resolve() // 网络错误时不阻断
  }
}, 500)

// 表单验证规则
const rules = {
  courseCode: [
    { required: true, message: t('education.course.courseCodeRequired'), trigger: 'blur' },
    { min: 1, max: 32, message: t('education.course.courseCodeLengthInvalid'), trigger: 'blur' },
    { validator: validateCourseCodeUnique, trigger: 'blur' }, // 异步验证
  ],
  courseName: [
    { required: true, message: t('education.course.courseNameRequired'), trigger: 'blur' },
    { min: 1, max: 128, message: t('education.course.courseNameLengthInvalid'), trigger: 'blur' },
  ],
}

// 获取课程详情
const getCourseInfo = async () => {
  if (!props.courseId) return

  loading.value = true
  try {
    const res = await getCourseDetail(props.courseId)
    if (res.code === 200) {
      const course = res.data
      Object.assign(form, {
        courseCode: course.courseCode,
        courseName: course.courseName,
        faculty: course.faculty,
        description: course.description,
        isPublic: course.isPublic,
        coverFileId: course.coverFileId,
      })
    }
  } catch (error) {
    message.error(t('education.course.getCourseDetailFailed'))
  } finally {
    loading.value = false
  }
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
    status: '0',
    teacherIds: [],
  })
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    if (isEdit.value) {
      // 修改课程（保持原有逻辑）
      const data: CourseUpdateDTO = {
        courseId: props.courseId!,
        courseCode: form.courseCode,
        courseName: form.courseName,
        faculty: form.faculty,
        description: form.description,
        isPublic: form.isPublic,
        coverFileId: form.coverFileId,
      }
      const res = await updateCourse(data)
      if (res.code === 200) {
        message.success(t('common.updateSuccess'))
        emit('success')
      }
    } else {
      // 新增模式：使用原子操作 API（包含教师关联）
      const data: CourseCreateDTO = {
        courseCode: form.courseCode!,
        courseName: form.courseName!,
        faculty: form.faculty,
        description: form.description,
        isPublic: form.isPublic,
        coverFileId: form.coverFileId,
        teacherIds: form.teacherIds || [],
      }
      const res = await addCourse(data)
      if (res.code === 200) {
        message.success(t('common.addSuccess'))
        emit('success')
      }
    }
  } catch (error: any) {
    if (error.errorFields) {
      // 表单验证失败
      return
    }
    message.error(isEdit.value ? t('common.updateFailed') : t('common.addFailed'))
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  emit('update:visible', false)
}

// 监听弹窗显示
watch(
  () => props.visible,
  (val) => {
    if (val) {
      if (isEdit.value) {
        getCourseInfo()
      }
    } else {
      resetForm()
    }
  }
)

// 组件挂载时加载选项
onMounted(() => {
  loadOptions()
})
</script>

<style scoped>
:deep(.ant-form-item) {
  margin-bottom: 16px;
}
</style>
