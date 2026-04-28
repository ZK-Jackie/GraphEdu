<template>
  <a-modal
    :open="visible"
    :title="t('common.assignCourse')"
    :width="800"
    :confirm-loading="submitting"
    destroy-on-close
    @ok="handleSubmit"
    @cancel="handleClose"
  >
    <a-spin :spinning="loadingStudents">
      <a-alert :message="t('education.student.assignTip')" type="info" show-icon class="mb-4" />

      <a-form layout="inline" class="mb-4">
        <a-form-item :label="t('common.realName')">
          <a-input
            v-model:value="searchName"
            :placeholder="t('common.realNamePlaceholder')"
            allow-clear
            style="width: 160px"
          />
        </a-form-item>
        <a-form-item :label="t('education.student.studentNo')">
          <a-input
            v-model:value="searchNo"
            :placeholder="t('education.student.studentNoPlaceholder')"
            allow-clear
            style="width: 160px"
          />
        </a-form-item>
      </a-form>

      <a-checkbox-group v-model:value="selectedStudentIds" style="width: 100%">
        <a-row :gutter="[16, 16]">
          <a-col v-for="student in filteredAllStudents" :key="student.studentId" :xs="24" :sm="12" :md="8">
            <a-checkbox :value="student.studentId" class="student-checkbox">
              <a-card size="small" :hoverable="true" class="student-card">
                <template #title>
                  <div class="student-title">{{ student.realName }}</div>
                </template>
                <div class="student-info">
                  <p class="student-field">
                    <span class="field-label">{{ t('education.student.studentNo') }}:</span>
                    <span class="field-value">{{ student.studentNo || '-' }}</span>
                  </p>
                  <p class="student-field">
                    <span class="field-label">{{ t('education.student.className') }}:</span>
                    <span class="field-value">{{ student.className || '-' }}</span>
                  </p>
                </div>
              </a-card>
            </a-checkbox>
          </a-col>
        </a-row>
      </a-checkbox-group>

      <a-empty v-if="filteredAllStudents.length === 0" :description="t('common.noData')" />
    </a-spin>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { getStudentList } from '@/api/education/student.ts'
import { batchAssignCourses } from '@/api/education/student_course.ts'

import type { StudentListVO } from '@/types/api/education/student.ts'

const { t } = useI18n()

interface Props {
  visible: boolean
  courseId: number
  existingStudentIds: number[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const loadingStudents = ref(false)
const submitting = ref(false)
const allStudents = ref<StudentListVO[]>([])
const selectedStudentIds = ref<number[]>([])
const searchName = ref('')
const searchNo = ref('')

const filteredAllStudents = computed(() => {
  let result = allStudents.value.filter((s) => !props.existingStudentIds.includes(s.studentId))
  if (searchName.value) {
    result = result.filter((s) => s.realName?.includes(searchName.value))
  }
  if (searchNo.value) {
    result = result.filter((s) => s.studentNo?.includes(searchNo.value))
  }
  return result
})

const loadAllStudents = async () => {
  loadingStudents.value = true
  try {
    const res = await getStudentList({ page: 1, size: 1000, status: '0' })
    if (res.code === 200) {
      allStudents.value = res.data.rows || []
    }
  } catch (_e) {
    message.error(t('education.student.loadStudentListFailed'))
  } finally {
    loadingStudents.value = false
  }
}

const handleSubmit = async () => {
  if (selectedStudentIds.value.length === 0) {
    message.warning(t('education.student.selectStudentTip'))
    return
  }

  submitting.value = true
  try {
    const res = await batchAssignCourses({
      studentIds: selectedStudentIds.value,
      courseId: props.courseId,
    })
    if (res.code === 200) {
      selectedStudentIds.value = []
      emit('success')
    }
  } catch (_e) {
    message.error(t('education.student.assignFailed'))
  } finally {
    submitting.value = false
  }
}

const handleClose = () => {
  selectedStudentIds.value = []
  emit('update:visible', false)
}

watch(
  () => props.visible,
  (newVal) => {
    if (newVal) loadAllStudents()
  }
)
</script>

<style scoped>
.student-checkbox {
  width: 100%;
}

.student-card {
  width: 100%;
  transition: all 0.3s;
}

.student-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.student-title {
  font-weight: 600;
  color: #262626;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.student-info {
  margin-top: 8px;
}

.student-field {
  margin: 4px 0;
  display: flex;
  align-items: center;
  font-size: 12px;
}

.field-label {
  color: #8c8c8c;
  min-width: 60px;
  margin-right: 8px;
}

.field-value {
  color: #262626;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
