<template>
  <a-spin :spinning="loading">
    <a-descriptions bordered :column="{ xs: 1, sm: 2, md: 3 }" size="middle">
      <a-descriptions-item :label="t('common.realName')">
        {{ student?.realName || '-' }}
      </a-descriptions-item>
      <a-descriptions-item :label="t('education.student.studentNo')">
        {{ student?.studentNo || '-' }}
      </a-descriptions-item>
      <a-descriptions-item :label="t('education.student.gender')">
        <DictTag v-if="student?.gender !== undefined" dict-type="sys_user_sex" :value="String(student.gender)" />
        <span v-else>-</span>
      </a-descriptions-item>
      <a-descriptions-item :label="t('common.faculty')">
        {{ student?.faculty || '-' }}
      </a-descriptions-item>
      <a-descriptions-item :label="t('education.student.major')">
        {{ student?.major || '-' }}
      </a-descriptions-item>
      <a-descriptions-item :label="t('education.student.grade')">
        {{ student?.grade || '-' }}
      </a-descriptions-item>
      <a-descriptions-item :label="t('education.student.className')">
        {{ student?.className || '-' }}
      </a-descriptions-item>
      <a-descriptions-item :label="t('education.student.studyStyle')">
        {{ student?.studyStyle || '-' }}
      </a-descriptions-item>
      <a-descriptions-item :label="t('education.student.studyHabit')">
        {{ student?.studyHabit || '-' }}
      </a-descriptions-item>
      <a-descriptions-item :label="t('education.student.totalStudyTime')" :span="3">
        {{ formatStudyTime(student?.totalStudyTime) }}
      </a-descriptions-item>
      <a-descriptions-item :label="t('education.student.courseCount')">
        {{ student?.courseCount ?? '-' }}
      </a-descriptions-item>
      <a-descriptions-item :label="t('common.status')">
        <DictTag v-if="student?.status" dict-type="sys_data_status" :value="student.status" />
        <span v-else>-</span>
      </a-descriptions-item>
      <a-descriptions-item v-if="student?.description" :label="t('education.student.description')" :span="3">
        {{ student.description }}
      </a-descriptions-item>
    </a-descriptions>
  </a-spin>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { getStudentDetail } from '@/api/education/student.ts'
import DictTag from '@/components/dict/DictTag.vue'
import type { StudentDetailVO } from '@/types/api/education/student.ts'

const { t } = useI18n()

interface Props {
  studentId?: number
}

const props = defineProps<Props>()

const loading = ref(false)
const student = ref<StudentDetailVO>()

const formatStudyTime = (minutes?: number | null) => {
  if (!minutes) return '-'
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  if (h > 0) return `${h}${t('common.hour')} ${m}${t('common.minute')}`
  return `${m}${t('common.minute')}`
}

const loadStudent = async () => {
  if (!props.studentId) return
  loading.value = true
  try {
    const res = await getStudentDetail(props.studentId)
    if (res.code === 200) {
      student.value = res.data
    }
  } catch (_e) {
    message.error(t('education.student.loadStudentFailed'))
  } finally {
    loading.value = false
  }
}

watch(
  () => props.studentId,
  (newId) => {
    if (newId) loadStudent()
  },
  { immediate: true }
)
</script>
