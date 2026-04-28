<template>
  <a-modal
    :visible="visible"
    :title="isEditMode ? '编辑 GraphRAG 任务' : '新增 GraphRAG 任务'"
    :width="700"
    :confirm-loading="submitting"
    @ok="handleSubmit"
    @cancel="handleCancel"
  >
    <a-form ref="formRef" :model="formData" :rules="formRules as any" :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }">
      <!-- 基本信息 -->
      <a-divider orientation="left">基本信息</a-divider>

      <a-form-item label="关联课程" name="courseId">
        <a-select
          v-model:value="formData.courseId"
          placeholder="请选择课程"
          :loading="courseLoading"
          :disabled="isEditMode"
          show-search
          :filter-option="filterCourseOption"
        >
          <a-select-option v-for="course in courseList" :key="course.courseId" :value="course.courseId">
            {{ course.courseName }} ({{ course.courseCode }})
          </a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="任务类型" name="taskType">
        <a-input
          v-model:value="formData.taskType"
          placeholder="请输入任务类型（如：graphrag_build、graphrag_update）"
          :disabled="isEditMode"
        />
      </a-form-item>

      <a-form-item label="文档ID列表" name="resourceIds">
        <a-select
          v-model:value="formData.resourceIds"
          mode="multiple"
          placeholder="请选择文档"
          :loading="resourceLoading"
          :disabled="isEditMode"
          show-search
          :filter-option="filterResourceOption"
        >
          <a-select-option v-for="resource in resourceList" :key="resource.resourceId" :value="resource.resourceId">
            {{ resource.resourceName }} (ID: {{ resource.resourceId }})
            <span v-if="resource.resourceType === 'text'"> - 无需转换 </span>
            <span v-else-if="resource.parseStatus === '2' || resource.parseStatus === 'completed'"> - 已转换 </span>
            <span v-else> - 需转换 </span>
          </a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item v-if="isEditMode" label="任务状态" name="taskStatus">
        <a-select v-model:value="formData.taskStatus" placeholder="请选择任务状态">
          <a-select-option value="pending">待处理</a-select-option>
          <a-select-option value="processing">处理中</a-select-option>
          <a-select-option value="success">成功</a-select-option>
          <a-select-option value="failed">失败</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item v-if="isEditMode" label="任务信息" name="taskMessage">
        <a-textarea v-model:value="formData.taskMessage" placeholder="任务信息或错误详情" :rows="3" />
      </a-form-item>

      <!-- 高级配置 -->
      <a-divider orientation="left">高级配置</a-divider>

      <a-form-item label="实体类型" name="entityTypes">
        <a-select
          v-model:value="formData.entityTypes"
          mode="tags"
          placeholder="请输入实体类型（可自定义添加）"
          :disabled="isEditMode"
        >
          <a-select-option value="概念">概念</a-select-option>
          <a-select-option value="原理">原理</a-select-option>
          <a-select-option value="方法">方法</a-select-option>
          <a-select-option value="公式">公式</a-select-option>
          <a-select-option value="例题">例题</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="提示词模板" name="promptTemplate">
        <a-select
          v-model:value="formData.promptTemplate"
          placeholder="请选择提示词模板"
          :disabled="isEditMode"
          allow-clear
        >
          <a-select-option value="default/en">默认英文模板</a-select-option>
          <a-select-option value="default/zh">默认中文模板</a-select-option>
          <a-select-option value="edu/en">教育英文模板</a-select-option>
          <a-select-option value="edu/zh">教育中文模板</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item v-if="isEditMode && taskDetail" label="统计信息">
        <div v-if="taskDetail.stats" class="stats-info">
          <a-descriptions size="small" :column="2" bordered>
            <a-descriptions-item v-if="taskDetail.stats.document_count" label="文档数量">
              {{ taskDetail.stats.document_count }}
            </a-descriptions-item>
            <a-descriptions-item v-if="taskDetail.stats.entity_count" label="实体数量">
              {{ taskDetail.stats.entity_count }}
            </a-descriptions-item>
            <a-descriptions-item v-if="taskDetail.stats.relation_count" label="关系数量">
              {{ taskDetail.stats.relation_count }}
            </a-descriptions-item>
            <a-descriptions-item v-if="taskDetail.stats.community_count" label="社区数量">
              {{ taskDetail.stats.community_count }}
            </a-descriptions-item>
          </a-descriptions>
        </div>
        <span v-else class="text-muted">暂无统计信息</span>
      </a-form-item>

      <a-form-item v-if="isEditMode && taskDetail" label="时间信息">
        <div class="time-info">
          <div v-if="taskDetail.createTime">
            <span class="label">创建时间：</span>{{ formatTime(taskDetail.createTime) }}
          </div>
          <div v-if="taskDetail.startTime">
            <span class="label">开始时间：</span>{{ formatTime(taskDetail.startTime) }}
          </div>
          <div v-if="taskDetail.endTime"><span class="label">结束时间：</span>{{ formatTime(taskDetail.endTime) }}</div>
        </div>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { message } from 'ant-design-vue'
import type { FormInstance } from 'ant-design-vue'
import { addGraphRAGTask, updateGraphRAGTask, getGraphRAGTaskDetail } from '@/api/education/graphRagTask.ts'
import { getCourseList } from '@/api/education/course.ts'
import { getChapterResourceList } from '@/api/education/chapterResource.ts'
import { parseTime } from '@/utils/common.ts'
import type { CourseListVO } from '@/types/api/education/course.ts'
import type { ChapterResourceListVO } from '@/types/api/education/chapterResource.ts'
import type {
  GraphRAGTaskCreateDTO,
  GraphRAGTaskDetailVO,
  GraphRAGTaskUpdateDTO,
} from '@/types/api/education/graphragTask.ts'

// Props
interface Props {
  visible: boolean
  taskId?: number
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  taskId: undefined,
})

// Emits
interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const emit = defineEmits<Emits>()

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const formData = reactive<GraphRAGTaskCreateDTO & GraphRAGTaskUpdateDTO>({
  taskId: undefined as any,
  courseId: undefined as any,
  resourceIds: [],
  taskType: '',
  taskStatus: undefined,
  taskMessage: undefined,
  entityTypes: [],
  promptTemplate: undefined,
  customPromptTemplate: undefined,
  stats: undefined,
  startTime: undefined,
  endTime: undefined,
})

// 表单验证规则
const formRules = {
  courseId: [{ required: true, message: '请选择课程', trigger: 'change' }],
  resourceIds: [
    {
      required: true,
      type: 'array' as const,
      min: 1,
      message: '请至少选择一个文档',
      trigger: 'change',
    },
  ],
  taskType: [{ required: true, message: '请输入任务类型', trigger: 'blur' }],
}

// 数据状态
const submitting = ref(false)
const courseLoading = ref(false)
const resourceLoading = ref(false)
const courseList = ref<CourseListVO[]>([])
const resourceList = ref<ChapterResourceListVO[]>([])
const taskDetail = ref<GraphRAGTaskDetailVO>()

// 是否为编辑模式
const isEditMode = computed(() => !!props.taskId)

// 获取课程列表
const loadCourseList = async () => {
  courseLoading.value = true
  try {
    const res = await getCourseList({
      page: 1,
      size: 1000,
      status: '0',
    })
    if (res.code === 200 && res.data) {
      courseList.value = res.data.rows || []
    }
  } catch (_e) {
    message.error('获取课程列表失败')
  } finally {
    courseLoading.value = false
  }
}

// 获取资源列表
const loadResourceList = async (courseId: number) => {
  if (!courseId) {
    resourceList.value = []
    return
  }

  resourceLoading.value = true
  try {
    const res = await getChapterResourceList({
      page: 1,
      size: 1000,
      courseId: courseId,
      status: '0',
    } as any)
    if (res.code === 200 && res.data) {
      resourceList.value = res.data.rows || []
    }
  } catch (_e) {
    message.error('获取资源列表失败')
  } finally {
    resourceLoading.value = false
  }
}

// 获取任务详情
const loadTaskDetail = async () => {
  if (!props.taskId) return

  try {
    const res = await getGraphRAGTaskDetail(props.taskId)
    if (res.code === 200 && res.data) {
      taskDetail.value = res.data

      // 填充表单数据
      formData.taskId = res.data.taskId
      formData.courseId = res.data.courseId
      formData.resourceIds = res.data.resourceIds || []
      formData.taskType = res.data.taskType
      formData.taskStatus = res.data.taskStatus as any
      formData.taskMessage = res.data.taskMessage
      formData.entityTypes = res.data.entityTypes || []
      formData.promptTemplate = res.data.promptTemplate
      formData.customPromptTemplate = res.data.customPromptTemplate
      formData.stats = res.data.stats
      formData.startTime = res.data.startTime
      formData.endTime = res.data.endTime

      // 加载该课程的资源列表
      loadResourceList(res.data.courseId)
    }
  } catch (_e) {
    message.error('获取任务详情失败')
  }
}

// 课程筛选
const filterCourseOption = (input: string, option: any) => {
  const course = courseList.value.find((c) => c.courseId === option.value)
  if (!course) return false
  return (
    course.courseName.toLowerCase().includes(input.toLowerCase()) ||
    course.courseCode.toLowerCase().includes(input.toLowerCase())
  )
}

// 资源筛选
const filterResourceOption = (input: string, option: any) => {
  const resource = resourceList.value.find((r) => r.resourceId === option.value)
  if (!resource) return false
  return resource.resourceName.toLowerCase().includes(input.toLowerCase())
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
  } catch (_e) {
    return
  }

  submitting.value = true
  try {
    if (isEditMode.value) {
      // 编辑
      const updateData: GraphRAGTaskUpdateDTO = {
        taskId: props.taskId!,
        taskStatus: formData.taskStatus,
        taskMessage: formData.taskMessage,
        entityTypes: formData.entityTypes,
        promptTemplate: formData.promptTemplate,
        customPromptTemplate: formData.customPromptTemplate,
        stats: formData.stats,
        startTime: formData.startTime,
        endTime: formData.endTime,
      }
      const res = await updateGraphRAGTask(updateData)
      if (res.code === 200) {
        message.success('更新成功')
        emit('success')
      }
    } else {
      // 新增
      const createData: GraphRAGTaskCreateDTO = {
        courseId: formData.courseId!,
        resourceIds: formData.resourceIds,
        taskType: formData.taskType,
        entityTypes: formData.entityTypes,
        promptTemplate: formData.promptTemplate,
        customPromptTemplate: formData.customPromptTemplate,
      }
      const res = await addGraphRAGTask(createData)
      if (res.code === 200) {
        message.success('新增成功')
        emit('success')
      }
    }
  } catch (_e) {
    message.error(isEditMode.value ? '更新失败' : '新增失败')
  } finally {
    submitting.value = false
  }
}

// 取消
const handleCancel = () => {
  emit('update:visible', false)
}

// 格式化时间
const formatTime = (time: string | undefined) => {
  if (!time) return ''
  return parseTime(time)
}

// 监听 visible 变化
watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      // 弹窗打开时
      if (isEditMode.value) {
        // 编辑模式：加载详情
        loadTaskDetail()
      } else {
        // 新增模式：重置表单
        formRef.value?.resetFields()
        taskDetail.value = undefined
      }
      // 加载课程列表
      loadCourseList()
    }
  }
)

// 监听 courseId 变化
watch(
  () => formData.courseId,
  (newVal) => {
    if (newVal && !isEditMode.value) {
      // 仅在新增模式下自动加载资源列表
      loadResourceList(newVal)
    }
  }
)
</script>

<style scoped>
.stats-info {
  padding: 8px;
  background: #f5f5f5;
  border-radius: 4px;
}

.time-info {
  font-size: 13px;
  line-height: 2;
}

.time-info .label {
  font-weight: 500;
  color: #333;
}

.text-muted {
  color: #999;
}

:deep(.ant-divider-horizontal.ant-divider-with-text-left) {
  margin: 16px 0;
}

:deep(.ant-form-item) {
  margin-bottom: 16px;
}
</style>
