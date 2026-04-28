<template>
  <div class="exercise-tab">
    <div class="toolbar">
      <a-space>
        <a-button type="primary" @click="handleAdd">
          <template #icon><PlusOutlined /></template>
          新增习题
        </a-button>
        <a-button @click="handleOpenAiModal">
          <template #icon><ThunderboltOutlined /></template>
          AI 出题
        </a-button>
        <a-button @click="loadExercises">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
      </a-space>
    </div>

    <a-table
      :data-source="rows"
      :loading="loading"
      row-key="exerciseId"
      :pagination="pagination"
      size="small"
      @change="handleTableChange"
    >
      <a-table-column key="exerciseId" title="ID" data-index="exerciseId" :width="88" />
      <a-table-column key="questionType" title="题型" :width="96" align="center">
        <template #default="{ record }">
          <DictTag :options="questionTypeDictOptions" :value="getQuestionType(record)" />
        </template>
      </a-table-column>
      <a-table-column key="title" title="题目标题" :ellipsis="true">
        <template #default="{ record }">
          {{ extractPrimaryQuestion(record.exercise)?.title || '未命名题目' }}
        </template>
      </a-table-column>
      <a-table-column key="content" title="题干" :ellipsis="true">
        <template #default="{ record }">
          {{ extractPrimaryQuestion(record.exercise)?.content || '-' }}
        </template>
      </a-table-column>
      <a-table-column key="source" title="来源" data-index="source" :width="130" :ellipsis="true" />
      <a-table-column key="status" title="状态" :width="110" align="center">
        <template #default="{ record }">
          <a-switch
            :checked="record.status === '0'"
            checked-children="正常"
            un-checked-children="停用"
            @change="(checked) => handleChangeStatus(record.exerciseId, checked === true)"
          />
        </template>
      </a-table-column>
      <a-table-column key="createTime" title="创建时间" :width="180">
        <template #default="{ record }">
          {{ parseTime(record.createTime) || '-' }}
        </template>
      </a-table-column>
      <a-table-column key="action" title="操作" :width="140" align="center" fixed="right">
        <template #default="{ record }">
          <a-space>
            <a-button type="link" size="small" @click="handleEdit(record)">编辑</a-button>
            <a-button type="link" size="small" danger @click="handleDelete(record)">删除</a-button>
          </a-space>
        </template>
      </a-table-column>
    </a-table>

    <a-modal
      v-model:open="formVisible"
      :title="isEdit ? '编辑习题' : '新增习题'"
      :confirm-loading="submitting"
      width="860px"
      @ok="handleSubmit"
      @cancel="formVisible = false"
    >
      <a-form :model="formModel" :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
        <a-form-item label="来源">
          <a-input v-model:value="formModel.source" placeholder="如：教师上传 / 系统生成" />
        </a-form-item>
        <a-form-item label="状态" v-if="isEdit">
          <a-radio-group v-model:value="formModel.status">
            <a-radio value="0">正常</a-radio>
            <a-radio value="1">停用</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="录入方式">
          <a-radio-group v-model:value="formModel.mode">
            <a-radio value="single">结构化单题</a-radio>
            <a-radio value="json">JSON（单题或题组）</a-radio>
          </a-radio-group>
        </a-form-item>

        <template v-if="formModel.mode === 'single'">
          <a-form-item label="题型">
            <a-select
              v-model:value="formModel.questionType"
              :options="questionTypeOptions"
              @change="(value) => handleQuestionTypeChange(value)"
            />
          </a-form-item>
          <a-form-item label="标题">
            <a-input v-model:value="formModel.title" placeholder="请输入题目标题" />
          </a-form-item>
          <a-form-item label="题干">
            <a-textarea v-model:value="formModel.content" :rows="4" placeholder="请输入题干" />
          </a-form-item>

          <template v-if="formModel.questionType === 'single' || formModel.questionType === 'multi'">
            <a-form-item label="选项">
              <div class="option-editor">
                <div v-for="(item, index) in formModel.optionItems" :key="index" class="option-row">
                  <a-tag color="blue" class="option-tag">{{ getOptionLetter(index) }}</a-tag>
                  <a-input
                    v-model:value="formModel.optionItems[index]"
                    :placeholder="`请输入选项 ${getOptionLetter(index)} 内容`"
                    @change="syncAnswerByOptions"
                  />
                  <a-button
                    type="text"
                    danger
                    :disabled="formModel.optionItems.length <= 2"
                    @click="removeOption(index)"
                  >
                    删除
                  </a-button>
                </div>
                <a-button type="dashed" block @click="addOption">+ 增加选项</a-button>
              </div>
            </a-form-item>

            <a-form-item label="答案" v-if="formModel.questionType === 'single'">
              <a-radio-group v-model:value="formModel.singleAnswer">
                <a-radio
                  v-for="option in optionChoiceOptions"
                  :key="option.value"
                  :value="option.value"
                  :disabled="!option.enabled"
                >
                  {{ option.value }}
                </a-radio>
              </a-radio-group>
            </a-form-item>

            <a-form-item label="答案" v-else>
              <a-checkbox-group v-model:value="formModel.multiAnswers">
                <a-checkbox
                  v-for="option in optionChoiceOptions"
                  :key="option.value"
                  :value="option.value"
                  :disabled="!option.enabled"
                >
                  {{ option.value }}
                </a-checkbox>
              </a-checkbox-group>
            </a-form-item>
          </template>

          <a-form-item label="答案" v-else-if="formModel.questionType === 'judge'">
            <a-radio-group v-model:value="formModel.judgeAnswer">
              <a-radio value="正确">正确</a-radio>
              <a-radio value="错误">错误</a-radio>
            </a-radio-group>
          </a-form-item>

          <a-form-item label="参考答案" v-else>
            <a-textarea v-model:value="formModel.essayAnswer" :rows="3" placeholder="请输入参考答案（可选）" />
          </a-form-item>

          <a-form-item label="解析">
            <a-textarea v-model:value="formModel.explanation" :rows="3" placeholder="答案解析（可选）" />
          </a-form-item>
        </template>

        <template v-else>
          <a-form-item label="JSON 内容">
            <a-textarea
              v-model:value="formModel.jsonText"
              :rows="14"
              placeholder="请输入 QuestionOptionContent 对象或数组的 JSON"
            />
          </a-form-item>
        </template>
      </a-form>
    </a-modal>

    <!-- AI 出题 Modal -->
    <a-modal
      v-model:open="aiModalVisible"
      title="AI 出题"
      :confirm-loading="aiSubmitting"
      :ok-text="aiTaskId ? '关闭' : '确定'"
      :cancel-button-props="{ style: { display: aiTaskId ? 'none' : '' } } as any"
      width="640px"
      @ok="handleAiModalOk"
      @cancel="handleAiModalCancel"
    >
      <!-- 生成进度 -->
      <div v-if="aiTaskId" class="ai-progress">
        <a-progress :percent="aiTaskPercent" :status="aiProgressStatus" />
        <p class="ai-progress-text">{{ aiTaskMessage || '处理中...' }}</p>
      </div>

      <!-- 表单（提交前） -->
      <a-form v-else :label-col="{ span: 5 }" :wrapper-col="{ span: 19 }">
        <a-form-item label="选择资料" required>
          <div v-if="aiResources.length === 0" class="text-gray-400 text-sm">暂无可选资料</div>
          <a-checkbox-group v-else v-model:value="aiFormModel.resourceIds" class="!flex flex-col gap-2">
            <a-checkbox v-for="res in aiResources" :key="res.resourceId" :value="res.resourceId">
              <a-tag>{{ res.resourceType }}</a-tag>
              {{ res.resourceName }}
            </a-checkbox>
          </a-checkbox-group>
        </a-form-item>
        <a-form-item label="题目类型">
          <a-select
            v-model:value="aiFormModel.questionType"
            :options="aiQuestionTypeOptions"
            placeholder="不限（由 AI 自动选择）"
            allow-clear
          />
        </a-form-item>
        <a-form-item label="难度">
          <a-select
            v-model:value="aiFormModel.difficulty"
            :options="aiDifficultyOptions"
            placeholder="不限（由 AI 自动选择）"
            allow-clear
          />
        </a-form-item>
        <a-form-item label="生成数量">
          <a-input-number v-model:value="aiFormModel.number" :min="1" :max="20" />
        </a-form-item>
        <a-form-item label="补充说明">
          <a-textarea
            v-model:value="aiFormModel.extraInfo"
            :rows="3"
            placeholder="对题目类型的额外描述或其他要求（可选）"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, ReloadOutlined, ThunderboltOutlined } from '@ant-design/icons-vue'
import type { TablePaginationConfig } from 'ant-design-vue'
import {
  addCourseExercise,
  batchGenerateExercises,
  changeCourseExerciseStatus,
  deleteCourseExercise,
  getCourseExerciseList,
  getGenerateProgress,
  updateCourseExercise,
} from '@/api/education/courseExercise.ts'
import { getResourcesByChapter } from '@/api/education/chapterResource.ts'
import DictTag from '@/components/dict/DictTag.vue'
import { parseTime } from '@/utils/common.ts'
import type {
  CourseExerciseCreateDTO,
  CourseExerciseListVO,
  CourseExerciseUpdateDTO,
} from '@/types/api/education/courseExercise.ts'
import type { ChapterResourceListVO } from '@/types/api/education/chapterResource.ts'
import type { QuestionOptionContent } from '@/types/api/education/agent.ts'

interface Props {
  courseId: number
  chapterId: number
}

type EditMode = 'single' | 'json'

const props = defineProps<Props>()

const loading = ref(false)
const submitting = ref(false)
const rows = ref<CourseExerciseListVO[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(10)

const formVisible = ref(false)
const isEdit = ref(false)
const formModel = reactive({
  exerciseId: 0,
  source: '',
  status: '0' as '0' | '1',
  mode: 'single' as EditMode,
  questionType: 'single',
  title: '',
  content: '',
  optionItems: ['', '', '', ''],
  singleAnswer: '',
  multiAnswers: [] as string[],
  judgeAnswer: '正确',
  essayAnswer: '',
  explanation: '',
  jsonText: '',
})

const questionTypeOptions = [
  { label: '单选题', value: 'single' },
  { label: '多选题', value: 'multi' },
  { label: '判断题', value: 'judge' },
  { label: '问答题', value: 'essay' },
]

/** 题型字典选项，用于 DictTag 渲染 */
const questionTypeDictOptions = [
  { label: '单选题', value: 'single', tagType: 'blue' },
  { label: '多选题', value: 'multi', tagType: 'purple' },
  { label: '判断题', value: 'judge', tagType: 'orange' },
  { label: '问答题', value: 'essay', tagType: 'green' },
]

const pagination = computed<TablePaginationConfig>(() => ({
  current: page.value,
  pageSize: size.value,
  total: total.value,
  showSizeChanger: true,
  showTotal: (v) => `共 ${v} 条`,
}))

const getOptionLetter = (index: number) => String.fromCharCode(65 + index)

const optionChoiceOptions = computed(() =>
  formModel.optionItems.map((item, index) => {
    const letter = getOptionLetter(index)
    return {
      value: letter,
      label: `${letter}. ${item || '(未填写)'}`,
      enabled: Boolean(item.trim()),
    }
  })
)

const isQuestionOptionContent = (value: unknown): value is QuestionOptionContent => {
  if (!value || typeof value !== 'object') return false
  const current = value as QuestionOptionContent
  return Array.isArray(current.options)
}

const extractPrimaryQuestion = (
  payload: QuestionOptionContent | QuestionOptionContent[] | null | undefined
): QuestionOptionContent | undefined => {
  if (!payload) return undefined
  if (Array.isArray(payload)) {
    return payload.find((item) => isQuestionOptionContent(item))
  }
  return isQuestionOptionContent(payload) ? payload : undefined
}

/** 从记录中提取题型，兼容 snake_case / camelCase */
const getQuestionType = (record: CourseExerciseListVO): string => {
  const q = extractPrimaryQuestion(record.exercise)
  // 后端可能返回 question_type（snake_case）或 questionType（camelCase）
  return (q as any)?.questionType || (q as any)?.question_type || ''
}

const loadExercises = async () => {
  if (!props.chapterId) {
    rows.value = []
    total.value = 0
    return
  }

  loading.value = true
  try {
    const res = await getCourseExerciseList({
      page: page.value,
      size: size.value,
      courseId: props.courseId,
      chapterId: props.chapterId,
    })
    if (res.code === 200) {
      rows.value = res.data?.rows ?? []
      total.value = res.data?.total ?? 0
    }
  } catch (_err) {
    message.error('加载习题列表失败')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  formModel.exerciseId = 0
  formModel.source = ''
  formModel.status = '0'
  formModel.mode = 'single'
  formModel.questionType = 'single'
  formModel.title = ''
  formModel.content = ''
  formModel.optionItems = ['', '', '', '']
  formModel.singleAnswer = ''
  formModel.multiAnswers = []
  formModel.judgeAnswer = '正确'
  formModel.essayAnswer = ''
  formModel.explanation = ''
  formModel.jsonText = ''
}

const handleAdd = () => {
  isEdit.value = false
  resetForm()
  formVisible.value = true
}

const fillSingleQuestionForm = (exercise: QuestionOptionContent | undefined) => {
  if (!exercise) return
  // 兼容 snake_case（后端）和 camelCase（前端）字段名
  const raw = exercise as any
  formModel.questionType = raw.questionType || raw.question_type || 'single'
  formModel.title = exercise.title || ''
  formModel.content = exercise.content || ''
  formModel.optionItems = (exercise.options || []).length > 0 ? [...exercise.options] : ['', '', '', '']

  const answers = exercise.answer || []
  const letters = answers.map((item) => item.trim()).filter((item) => item.length > 0)

  if (formModel.questionType === 'single' || formModel.questionType === 'multi') {
    const validLetters = letters
      .map((answer) => {
        if (/^[A-Z]$/.test(answer)) return answer
        const optionIndex = formModel.optionItems.findIndex((option) => option.trim() === answer)
        return optionIndex >= 0 ? getOptionLetter(optionIndex) : ''
      })
      .filter((item) => item)

    if (formModel.questionType === 'single') {
      formModel.singleAnswer = validLetters[0] || ''
      formModel.multiAnswers = []
    } else {
      formModel.multiAnswers = validLetters
      formModel.singleAnswer = ''
    }
  } else if (formModel.questionType === 'judge') {
    formModel.judgeAnswer = letters[0] === '错误' ? '错误' : '正确'
  } else {
    formModel.essayAnswer = letters[0] || ''
  }

  formModel.explanation = exercise.explanation || ''
  syncAnswerByOptions()
}

const handleEdit = (record: CourseExerciseListVO) => {
  isEdit.value = true
  resetForm()

  formModel.exerciseId = record.exerciseId
  formModel.source = record.source || ''
  formModel.status = (record.status === '1' ? '1' : '0') as '0' | '1'

  if (Array.isArray(record.exercise)) {
    formModel.mode = 'json'
    formModel.jsonText = JSON.stringify(record.exercise, null, 2)
  } else {
    formModel.mode = 'single'
    fillSingleQuestionForm(extractPrimaryQuestion(record.exercise))
    if (!formModel.title && record.exercise) {
      formModel.mode = 'json'
      formModel.jsonText = JSON.stringify(record.exercise, null, 2)
    }
  }

  formVisible.value = true
}

const syncAnswerByOptions = () => {
  const validValues = formModel.optionItems
    .map((option, index) => (option.trim() ? getOptionLetter(index) : ''))
    .filter((item) => item)

  if (formModel.questionType === 'single' && formModel.singleAnswer && !validValues.includes(formModel.singleAnswer)) {
    formModel.singleAnswer = ''
  }

  if (formModel.questionType === 'multi') {
    formModel.multiAnswers = formModel.multiAnswers.filter((item) => validValues.includes(item))
  }
}

const addOption = () => {
  formModel.optionItems.push('')
  syncAnswerByOptions()
}

const removeOption = (index: number) => {
  if (formModel.optionItems.length <= 2) return
  formModel.optionItems.splice(index, 1)
  syncAnswerByOptions()
}

const handleQuestionTypeChange = (value: unknown) => {
  let normalized = ''
  if (typeof value === 'string' || typeof value === 'number') {
    normalized = String(value)
  } else if (value && typeof value === 'object' && 'value' in value) {
    normalized = String((value as { value?: string | number }).value || '')
  }

  if (!normalized) return
  formModel.questionType = normalized
  if (normalized === 'single' || normalized === 'multi') {
    if (!formModel.optionItems.length) {
      formModel.optionItems = ['', '', '', '']
    }
    if (normalized === 'single') {
      formModel.singleAnswer = formModel.multiAnswers[0] || formModel.singleAnswer
      formModel.multiAnswers = []
    } else {
      const first = formModel.singleAnswer
      formModel.multiAnswers = first ? [first] : []
      formModel.singleAnswer = ''
    }
    syncAnswerByOptions()
  }
}

const buildSingleQuestionPayload = (): QuestionOptionContent => {
  const type = formModel.questionType
  const options = formModel.optionItems.map((item) => item.trim()).filter((item) => item.length > 0)

  let answers: string[] = []

  if (type === 'single') {
    answers = formModel.singleAnswer ? [formModel.singleAnswer] : []
  } else if (type === 'multi') {
    answers = [...formModel.multiAnswers]
  } else if (type === 'judge') {
    answers = [formModel.judgeAnswer]
  } else if (type === 'essay' && formModel.essayAnswer.trim()) {
    answers = [formModel.essayAnswer.trim()]
  }

  const isEssay = formModel.questionType === 'essay'

  if (!formModel.title.trim()) {
    throw new Error('请填写题目标题')
  }
  if (!formModel.content.trim()) {
    throw new Error('请填写题干')
  }
  if ((type === 'single' || type === 'multi') && formModel.optionItems.some((item) => !item.trim())) {
    throw new Error('请完整填写所有选项内容')
  }
  if (!isEssay && (type === 'single' || type === 'multi') && options.length < 2) {
    throw new Error('选择题至少需要 2 个选项')
  }
  if (type === 'single' && answers.length !== 1) {
    throw new Error('单选题请只选择 1 个正确答案')
  }
  if (type === 'multi' && answers.length < 1) {
    throw new Error('多选题请至少选择 1 个正确答案')
  }

  return {
    questionType: type,
    title: formModel.title.trim(),
    content: formModel.content.trim(),
    options,
    answer: answers.length > 0 ? answers : null,
    explanation: formModel.explanation.trim() || undefined,
  }
}

const buildExercisePayload = (): QuestionOptionContent | QuestionOptionContent[] => {
  if (formModel.mode === 'single') {
    return buildSingleQuestionPayload()
  }

  try {
    const parsed = JSON.parse(formModel.jsonText)
    if (Array.isArray(parsed)) {
      if (!parsed.every((item) => isQuestionOptionContent(item))) {
        throw new Error('JSON 数组元素必须是 QuestionOptionContent 结构')
      }
      return parsed
    }

    if (!isQuestionOptionContent(parsed)) {
      throw new Error('JSON 必须是 QuestionOptionContent 对象或数组')
    }

    return parsed
  } catch (err: any) {
    throw new Error(err?.message || 'JSON 格式不正确')
  }
}

const handleSubmit = async () => {
  if (!props.courseId || !props.chapterId) {
    message.warning('缺少课程或章节信息')
    return
  }

  let exercisePayload: QuestionOptionContent | QuestionOptionContent[]
  try {
    exercisePayload = buildExercisePayload()
  } catch (err: any) {
    message.warning(err?.message || '请检查习题内容')
    return
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      const updateData: CourseExerciseUpdateDTO = {
        exerciseId: formModel.exerciseId,
        chapterId: props.chapterId,
        exercise: exercisePayload,
        source: formModel.source.trim() || undefined,
        status: formModel.status,
      }
      const res = await updateCourseExercise(updateData)
      if (res.code === 200) {
        message.success('习题更新成功')
      }
    } else {
      const createData: CourseExerciseCreateDTO = {
        courseId: props.courseId,
        chapterId: props.chapterId,
        exercise: exercisePayload,
        source: formModel.source.trim() || undefined,
      }
      const res = await addCourseExercise(createData)
      if (res.code === 200) {
        message.success('习题新增成功')
      }
    }

    formVisible.value = false
    await loadExercises()
  } catch (_err) {
    message.error(isEdit.value ? '习题更新失败' : '习题新增失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = (record: CourseExerciseListVO) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定删除习题 #${record.exerciseId} 吗？`,
    onOk: async () => {
      try {
        const res = await deleteCourseExercise(String(record.exerciseId))
        if (res.code === 200) {
          message.success('删除成功')
          await loadExercises()
        }
      } catch (_err) {
        message.error('删除失败')
      }
    },
  })
}

const handleChangeStatus = async (exerciseId: number, checked: boolean) => {
  const status = checked ? '0' : '1'
  try {
    const res = await changeCourseExerciseStatus({ exerciseId, status })
    if (res.code === 200) {
      message.success('状态更新成功')
      await loadExercises()
    }
  } catch (_err) {
    message.error('状态更新失败')
  }
}

const handleTableChange = (pager: TablePaginationConfig) => {
  page.value = pager.current || 1
  size.value = pager.pageSize || 10
  loadExercises()
}

// ==================== AI 出题 ====================

const aiModalVisible = ref(false)
const aiSubmitting = ref(false)
const aiResources = ref<ChapterResourceListVO[]>([])
const aiFormModel = reactive({
  resourceIds: [] as number[],
  questionType: undefined as string | undefined,
  difficulty: undefined as string | undefined,
  number: 1,
  extraInfo: '',
})

// 异步任务状态
const aiTaskId = ref<string | null>(null)
const aiTaskPercent = ref(0)
const aiTaskMessage = ref<string | null>(null)
const aiPollTimer = ref<number | null>(null)

const aiQuestionTypeOptions = [
  { label: '单选题', value: 'single' },
  { label: '多选题', value: 'multi' },
  { label: '判断题', value: 'judge' },
]

const aiDifficultyOptions = [
  { label: '简单', value: '简单' },
  { label: '中等', value: '中等' },
  { label: '困难', value: '困难' },
]

const aiProgressStatus = computed(() => {
  if (!aiTaskId.value) return 'normal'
  const msg = aiTaskMessage.value || ''
  if (msg.includes('失败') || msg.includes('错误')) return 'exception'
  if (aiTaskPercent.value >= 100) return 'success'
  return 'active'
})

const resetAiForm = () => {
  aiFormModel.resourceIds = []
  aiFormModel.questionType = undefined
  aiFormModel.difficulty = undefined
  aiFormModel.number = 1
  aiFormModel.extraInfo = ''
  aiTaskId.value = null
  aiTaskPercent.value = 0
  aiTaskMessage.value = null
}

const clearAiPollTimer = () => {
  if (aiPollTimer.value !== null) {
    window.clearInterval(aiPollTimer.value)
    aiPollTimer.value = null
  }
}

const isAiRunning = (status: string) => status === 'pending' || status === 'processing'

const pollAiProgress = async () => {
  if (!aiTaskId.value) return
  try {
    const res = await getGenerateProgress(aiTaskId.value)
    if (res.code === 200 && res.data) {
      const { taskStatus, progressPercent, generatedCount, message: msg } = res.data
      aiTaskPercent.value = progressPercent || 0
      aiTaskMessage.value = msg || null

      if (!isAiRunning(taskStatus)) {
        clearAiPollTimer()
        if (taskStatus === 'success') {
          aiTaskPercent.value = 100
          aiTaskMessage.value = `成功生成 ${generatedCount} 道题目`
          message.success(`成功生成 ${generatedCount} 道题目`)
          await loadExercises()
        } else if (taskStatus === 'failed') {
          message.error(msg || 'AI 出题失败')
        }
      }
    }
  } catch (_err) {
    clearAiPollTimer()
    aiTaskMessage.value = '查询生成进度失败'
  }
}

const startAiPolling = () => {
  clearAiPollTimer()
  aiPollTimer.value = window.setInterval(pollAiProgress, 3000)
  pollAiProgress()
}

const handleOpenAiModal = async () => {
  if (!props.chapterId) {
    message.warning('请先选择章节')
    return
  }

  resetAiForm()
  aiModalVisible.value = true

  try {
    const res = await getResourcesByChapter(props.chapterId)
    if (res.code === 200) {
      aiResources.value = Array.isArray(res.data) ? res.data : []
    }
  } catch (_err) {
    message.error('加载章节资料失败')
  }
}

const handleAiModalOk = () => {
  if (aiTaskId.value) {
    // 已提交任务，点击关闭
    aiModalVisible.value = false
    return
  }

  // 提交新任务
  if (aiFormModel.resourceIds.length === 0) {
    message.warning('请至少选择一个资料')
    return
  }

  aiSubmitting.value = true
  batchGenerateExercises({
    courseId: props.courseId,
    chapterId: props.chapterId,
    resourceIds: aiFormModel.resourceIds,
    difficulty: aiFormModel.difficulty,
    questionType: aiFormModel.questionType as 'single' | 'judge' | 'multi' | undefined,
    number: aiFormModel.number,
    extraInfo: aiFormModel.extraInfo || undefined,
  })
    .then((res) => {
      if (res.code === 200 && res.data?.taskId) {
        aiTaskId.value = res.data.taskId
        aiTaskMessage.value = '任务已提交，正在生成中...'
        aiTaskPercent.value = 5
        startAiPolling()
      }
    })
    .catch(() => {
      message.error('AI 出题任务提交失败，请稍后重试')
    })
    .finally(() => {
      aiSubmitting.value = false
    })
}

const handleAiModalCancel = () => {
  clearAiPollTimer()
  aiModalVisible.value = false
}

watch(
  () => [props.courseId, props.chapterId] as const,
  () => {
    page.value = 1
    loadExercises()
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  clearAiPollTimer()
})
</script>

<style scoped>
.exercise-tab {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
}

.option-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.option-tag {
  min-width: 28px;
  text-align: center;
}

.ai-progress {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 24px 0;
}

.ai-progress-text {
  text-align: center;
  color: rgba(0, 0, 0, 0.45);
  margin: 0;
}
</style>
