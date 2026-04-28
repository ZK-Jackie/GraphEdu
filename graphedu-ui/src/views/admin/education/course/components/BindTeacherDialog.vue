<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { getTeacherList } from '@/api/education/teacher.ts'
import { getCourseTeachers, bindCourseTeachers, unbindCourseTeachers } from '@/api/education/course.ts'

import type { TeacherListVO } from '@/types/api/education/teacher.ts'

const { t } = useI18n()

interface Props {
  visible: boolean
  courseId: number | null | undefined
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 状态
const loading = ref(false)
const saving = ref(false)
const teacherList = ref<TeacherListVO[]>([])
const selectedTeacherIds = ref<number[]>([])
const boundTeacherIds = ref<number[]>([])

// 计算属性
const title = computed(() => `${t('education.course.bindTeachers')} - ${props.courseId}`)

// 加载教师列表
const loadTeacherList = async () => {
  loading.value = true
  try {
    // 获取所有教师列表
    const res = await getTeacherList({ page: 1, size: 1000 })
    if (res.code === 200) {
      teacherList.value = res.data.rows || []
    }
  } catch (error) {
    console.error('加载教师列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载已绑定的教师
const loadBoundTeachers = async () => {
  if (!props.courseId) return

  try {
    const res = await getCourseTeachers(props.courseId)
    if (res.code === 200) {
      boundTeacherIds.value = res.data.map((teacher) => teacher.teacherId)
      selectedTeacherIds.value = [...boundTeacherIds.value]
    }
  } catch (error) {
    console.error('加载已绑定教师失败:', error)
  }
}

// 处理确定按钮
const handleOk = async () => {
  if (!props.courseId) return

  saving.value = true
  try {
    // 计算需要绑定和解绑的教师
    const toBind = selectedTeacherIds.value.filter((id) => !boundTeacherIds.value.includes(id))
    const toUnbind = boundTeacherIds.value.filter((id) => !selectedTeacherIds.value.includes(id))

    // 执行解绑操作
    if (toUnbind.length > 0) {
      await unbindCourseTeachers(props.courseId, toUnbind)
    }

    // 执行绑定操作
    if (toBind.length > 0) {
      await bindCourseTeachers(props.courseId, toBind)
    }

    message.success(t('common.success'))
    emit('success')
    handleCancel()
  } catch (error) {
    console.error('绑定教师失败:', error)
    message.error(t('education.course.bindTeachersFailed'))
  } finally {
    saving.value = false
  }
}

// 处理取消按钮
const handleCancel = () => {
  emit('update:visible', false)
  selectedTeacherIds.value = []
  boundTeacherIds.value = []
}

// 监听对话框显示状态
watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      loadTeacherList()
      loadBoundTeachers()
    }
  }
)
</script>

<template>
  <a-modal :open="visible" :title="title" :confirm-loading="saving" :width="800" @cancel="handleCancel" @ok="handleOk">
    <a-spin :spinning="loading" :tip="t('common.loading')">
      <div class="bind-teacher-dialog">
        <a-alert :message="t('education.course.bindTeachersHint')" type="info" show-icon style="margin-bottom: 16px" />

        <a-checkbox-group v-model:value="selectedTeacherIds" style="width: 100%">
          <a-row :gutter="[16, 16]">
            <a-col v-for="teacher in teacherList" :key="teacher.teacherId" :xs="24" :sm="12" :md="12" :lg="12" :xl="8">
              <a-checkbox :value="teacher.teacherId" class="teacher-checkbox">
                <a-card size="small" :hoverable="true" class="teacher-card">
                  <template #title>
                    <div class="teacher-title">{{ teacher.realName }}</div>
                  </template>
                  <div class="teacher-info">
                    <p class="teacher-field">
                      <span class="field-label">{{ t('education.teacher.teacherNo') }}:</span>
                      <span class="field-value">{{ teacher.teacherNo || '-' }}</span>
                    </p>
                    <p class="teacher-field">
                      <span class="field-label">{{ t('common.faculty') }}:</span>
                      <span class="field-value">{{ teacher.faculty || '-' }}</span>
                    </p>
                    <p class="teacher-field">
                      <span class="field-label">{{ t('education.teacher.jobTitle') }}:</span>
                      <span class="field-value">{{ teacher.title || '-' }}</span>
                    </p>
                  </div>
                </a-card>
              </a-checkbox>
            </a-col>
          </a-row>
        </a-checkbox-group>

        <a-empty v-if="teacherList.length === 0" :description="t('education.teacher.noTeachers')" />
      </div>
    </a-spin>
  </a-modal>
</template>

<style scoped>
.bind-teacher-dialog {
  max-height: 500px;
  overflow-y: auto;
}

.teacher-checkbox {
  width: 100%;
}

.teacher-card {
  width: 100%;
  transition: all 0.3s;
}

.teacher-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.teacher-title {
  font-weight: 600;
  color: #262626;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.teacher-info {
  margin-top: 8px;
}

.teacher-field {
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
