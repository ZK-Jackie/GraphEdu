<template>
  <div class="portal-manage-page">
    <a-spin v-if="loading" tip="加载中..." class="spin-center" />

    <template v-else>
      <!-- 页面头部 -->
      <a-page-header title="课程门户设置" :sub-title="courseName">
        <template #extra>
          <a-space>
            <a-button @click="handleReset">
              <template #icon><ReloadOutlined /></template>
              重置
            </a-button>
            <a-button type="primary" :loading="saving" @click="handleSave">
              <template #icon><SaveOutlined /></template>
              保存
            </a-button>
          </a-space>
        </template>
      </a-page-header>

      <!-- 表单内容 -->
      <div class="form-content">
        <a-form ref="formRef" :model="form" :rules="rules as any" :label-col="{ span: 4 }" :wrapper-col="{ span: 16 }">
          <!-- 基础信息 -->
          <a-card title="基础信息" class="form-card" :bordered="false">
            <a-row>
              <a-col :span="24">
                <a-form-item label="课程代码" name="courseCode">
                  <a-input v-model:value="form.courseCode" placeholder="请输入课程代码" :maxlength="32" allow-clear />
                </a-form-item>
              </a-col>
            </a-row>

            <a-row>
              <a-col :span="24">
                <a-form-item label="课程名称" name="courseName">
                  <a-input v-model:value="form.courseName" placeholder="请输入课程名称" :maxlength="128" allow-clear />
                </a-form-item>
              </a-col>
            </a-row>

            <a-row>
              <a-col :span="24">
                <a-form-item label="所属学院" name="faculty">
                  <a-input v-model:value="form.faculty" placeholder="请输入所属学院" :maxlength="64" allow-clear />
                </a-form-item>
              </a-col>
            </a-row>

            <a-row>
              <a-col :span="24">
                <a-form-item label="课程分类" name="category">
                  <a-input v-model:value="form.category" placeholder="请输入课程分类" :maxlength="64" allow-clear />
                </a-form-item>
              </a-col>
            </a-row>

            <a-row>
              <a-col :span="24">
                <a-form-item label="课程描述" name="description">
                  <a-textarea
                    v-model:value="form.description"
                    placeholder="请输入课程描述"
                    :rows="4"
                    :maxlength="500"
                    show-count
                    allow-clear
                  />
                </a-form-item>
              </a-col>
            </a-row>
          </a-card>

          <!-- 课程属性 -->
          <a-card title="课程属性" class="form-card" :bordered="false">
            <a-row>
              <a-col :span="24">
                <a-form-item label="难度级别" name="difficultyLevel">
                  <a-radio-group v-model:value="form.difficultyLevel">
                    <a-radio value="1">初级</a-radio>
                    <a-radio value="2">中级</a-radio>
                    <a-radio value="3">高级</a-radio>
                  </a-radio-group>
                </a-form-item>
              </a-col>
            </a-row>

            <a-row>
              <a-col :span="24">
                <a-form-item label="总学时" name="totalHours">
                  <a-input-number
                    v-model:value="form.totalHours"
                    placeholder="请输入总学时"
                    :min="0"
                    :precision="0"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
            </a-row>
          </a-card>

          <!-- 详细信息 -->
          <a-card title="详细信息" class="form-card" :bordered="false">
            <a-row>
              <a-col :span="24">
                <a-form-item label="课程大纲" name="courseOutline">
                  <a-textarea
                    v-model:value="form.courseOutline"
                    placeholder="请输入课程大纲"
                    :rows="6"
                    :maxlength="2000"
                    show-count
                    allow-clear
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <a-row>
              <a-col :span="24">
                <a-form-item label="适用人群" name="targetAudience">
                  <a-textarea
                    v-model:value="form.targetAudience"
                    placeholder="请输入适用人群"
                    :rows="4"
                    :maxlength="1000"
                    show-count
                    allow-clear
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <a-row>
              <a-col :span="24">
                <a-form-item label="学习目标" name="learningGoals">
                  <a-textarea
                    v-model:value="form.learningGoals"
                    placeholder="请输入学习目标"
                    :rows="4"
                    :maxlength="1000"
                    show-count
                    allow-clear
                  />
                </a-form-item>
              </a-col>
            </a-row>
          </a-card>

          <!-- 其他设置 -->
          <a-card title="其他设置" class="form-card" :bordered="false">
            <a-row>
              <a-col :span="24">
                <a-form-item label="课程标签" name="tags">
                  <a-select
                    v-model:value="form.tags"
                    mode="tags"
                    placeholder="请输入课程标签，按回车添加"
                    :max-tag-count="5"
                    allow-clear
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <a-row>
              <a-col :span="24">
                <a-form-item label="封面图片" name="coverFileId">
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

            <a-row>
              <a-col :span="24">
                <a-form-item label="是否公开" name="isPublic">
                  <DictRadio v-model:model-value="form.isPublic" dict-type="sys_data_option" />
                </a-form-item>
              </a-col>
            </a-row>

            <a-row>
              <a-col :span="24">
                <a-form-item label="课程状态" name="status">
                  <DictRadio v-model:model-value="form.status" dict-type="sys_data_status" />
                </a-form-item>
              </a-col>
            </a-row>
          </a-card>
        </a-form>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { SaveOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { useDebounceFn } from '@vueuse/core'
import type { FormInstance } from 'ant-design-vue'
import { getCourseDetail, updateCourse, checkCourseCodeExists } from '@/api/education/course'
import DictRadio from '@/components/dict/DictRadio.vue'
import FileUpload from '@/components/FileUpload/index.vue'
import type { CourseUpdateDTO } from '@/types/api/education/course.ts'

const route = useRoute()

// 课程ID
const courseId = ref<number>(Number(route.params.courseId) || 0)
const courseName = ref<string>('')
const loading = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()

// 表单数据
const form = reactive<Partial<CourseUpdateDTO>>({
  courseCode: '',
  courseName: '',
  faculty: '',
  description: '',
  category: '',
  difficultyLevel: '1',
  totalHours: 0,
  courseOutline: '',
  targetAudience: '',
  learningGoals: '',
  tags: [],
  coverFileId: undefined,
  isPublic: 'Y',
  status: '0',
})

// 原始数据（用于重置）
const originalData = ref<Partial<CourseUpdateDTO>>({})

// 异步验证课程代码唯一性（防抖 500ms）
const validateCourseCodeUnique = useDebounceFn(async (_rule: any, value: string) => {
  if (!value) {
    return Promise.resolve()
  }

  try {
    const res = await checkCourseCodeExists(value, courseId.value)
    if (res.code === 200 && res.data) {
      return Promise.reject(new Error('课程代码已存在'))
    }
    return Promise.resolve()
  } catch (error) {
    return Promise.resolve() // 网络错误时不阻断
  }
}, 500)

// 表单验证规则
const rules = {
  courseCode: [
    { required: true, message: '请输入课程代码', trigger: 'blur' },
    { min: 1, max: 32, message: '长度在 1 到 32 个字符', trigger: 'blur' },
    { validator: validateCourseCodeUnique, trigger: 'blur' },
  ],
  courseName: [
    { required: true, message: '请输入课程名称', trigger: 'blur' },
    { min: 1, max: 128, message: '长度在 1 到 128 个字符', trigger: 'blur' },
  ],
}

// 加载课程详情
const loadCourse = async () => {
  if (!courseId.value) {
    message.error('缺少课程ID参数')
    return
  }

  loading.value = true
  try {
    const res = await getCourseDetail(courseId.value)
    if (res.code === 200) {
      const course = res.data
      courseName.value = course.courseName

      // 填充表单数据
      Object.assign(form, {
        courseCode: course.courseCode,
        courseName: course.courseName,
        faculty: course.faculty,
        description: course.description,
        category: course.category,
        difficultyLevel: course.difficultyLevel || '1',
        totalHours: course.totalHours,
        courseOutline: course.courseOutline,
        targetAudience: course.targetAudience,
        learningGoals: course.learningGoals,
        tags: course.tags,
        coverFileId: course.coverFileId,
        isPublic: course.isPublic,
        status: course.status,
      })

      // 保存原始数据
      originalData.value = { ...form }
    }
  } catch (error) {
    message.error('加载课程信息失败')
  } finally {
    loading.value = false
  }
}

// 保存课程信息
const handleSave = async () => {
  try {
    await formRef.value?.validate()
    saving.value = true

    const data: CourseUpdateDTO = {
      courseId: courseId.value,
      courseCode: form.courseCode,
      courseName: form.courseName,
      faculty: form.faculty,
      description: form.description,
      category: form.category,
      difficultyLevel: form.difficultyLevel,
      totalHours: form.totalHours,
      courseOutline: form.courseOutline,
      targetAudience: form.targetAudience,
      learningGoals: form.learningGoals,
      tags: form.tags,
      coverFileId: form.coverFileId,
      isPublic: form.isPublic,
      status: form.status,
    }

    const res = await updateCourse(data)
    if (res.code === 200) {
      message.success('保存成功')
      originalData.value = { ...form }
    }
  } catch (error: any) {
    if (error.errorFields) {
      // 表单验证失败
      return
    }
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 重置表单
const handleReset = () => {
  Object.assign(form, originalData.value)
  formRef.value?.clearValidate()
  message.info('已重置为原始数据')
}

onMounted(() => {
  loadCourse()
})
</script>

<style scoped>
.portal-manage-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.spin-center {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  width: 100%;
}

.form-content {
  flex: 1;
  padding: 0 24px 24px;
  overflow-y: auto;
}

.form-card {
  margin-bottom: 16px;
  border-radius: 8px;
}

:deep(.ant-form-item) {
  margin-bottom: 16px;
}

:deep(.ant-card-body) {
  padding: 24px;
}

:deep(.ant-page-header) {
  padding: 16px 24px;
  background: var(--ge-bg-container);
  border-bottom: 1px solid var(--ge-border-color);
}
</style>
