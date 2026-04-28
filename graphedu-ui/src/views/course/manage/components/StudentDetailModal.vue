<template>
  <a-modal
    :open="visible"
    :title="`${t('education.student.studentDetail')} - ${studentName}`"
    :width="1200"
    :footer="null"
    destroy-on-close
    @cancel="handleClose"
  >
    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="profile" :tab="t('education.student.personalInfo')">
        <StudentProfileTab v-if="studentId" :student-id="studentId" />
      </a-tab-pane>
      <a-tab-pane key="learning" :tab="t('education.student.chapterLearning')">
        <StudentChapterLearningTab v-if="studentId && courseId" :course-id="courseId" :student-id="studentId" />
      </a-tab-pane>
    </a-tabs>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import StudentProfileTab from './StudentProfileTab.vue'
import StudentChapterLearningTab from './StudentChapterLearningTab.vue'

const { t } = useI18n()

interface Props {
  courseId: number
  studentId?: number
  studentName?: string
  visible: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

const activeTab = ref('profile')

const studentName = computed(() => props.studentName || '-')

const handleClose = () => {
  activeTab.value = 'profile'
  emit('update:visible', false)
}
</script>
