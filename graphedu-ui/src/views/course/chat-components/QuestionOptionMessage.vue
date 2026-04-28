<script setup lang="ts">
/**
 * QuestionOptionMessage - 题目交互组件
 *
 * options 数组中的字符串已包含选项前缀（如 "A. xxx"），
 * 渲染时直接显示原始文本，不再额外添加 A/B/C/D 前缀。
 */

import { computed, ref } from 'vue'
import { message } from 'ant-design-vue'
import { submitExerciseAttempt } from '@/api/education/exerciseAttempt'
import type { QuestionOptionContent, QuestionType } from '@/types/api/education/agent.ts'

const props = defineProps<{
  content: string
  metadata?: Record<string, any> | null
  /** 关联题库中的习题ID，有值时提交作答会记录到后端 */
  exerciseId?: number | null
}>()

const submitLoading = ref(false)

function normalizeOptionText(raw: string): string {
  return raw
    .trim()
    .replace(/^[A-Z][.、:\-\s]+/i, '')
    .replace(/\s+/g, ' ')
    .toLowerCase()
}

function optionKey(index: number): string {
  return String.fromCharCode(65 + index)
}

function parseQuestionPayload(content: string, metadata?: Record<string, any> | null): QuestionOptionContent {
  const rawQuestion = metadata?.questionOption || metadata?.question_option || metadata || null

  if (rawQuestion && Array.isArray(rawQuestion.options)) {
    return {
      title: rawQuestion.title,
      content: rawQuestion.content,
      options: rawQuestion.options,
      answer: rawQuestion.answer,
      questionType: rawQuestion.questionType || rawQuestion.question_type,
    }
  }

  try {
    const parsed = JSON.parse(content)
    if (parsed && Array.isArray(parsed.options)) {
      return {
        title: parsed.title,
        content: parsed.content,
        options: parsed.options,
        answer: parsed.answer,
        questionType: parsed.questionType || parsed.question_type,
      }
    }
  } catch {
    // 文本消息透传到题型分支时，保持兜底渲染
  }

  return {
    content,
    options: [],
    answer: null,
  }
}

const question = computed(() => parseQuestionPayload(props.content, props.metadata))

const inferredQuestionType = computed<QuestionType>(() => {
  const explicitType = question.value.questionType
  if (explicitType === 'single' || explicitType === 'multi' || explicitType === 'judge' || explicitType === 'essay') {
    return explicitType
  }

  // 无选项且无答案列表时推断为简答题
  if (!question.value.options?.length) {
    return 'essay'
  }

  const options = question.value.options.map((item) => normalizeOptionText(item))
  const judgeTokens = ['对', '错', '正确', '错误', '是', '否', 'true', 'false', 'yes', 'no']
  const isJudgeByOptions = options.length === 2 && options.every((item) => judgeTokens.includes(item))

  if (isJudgeByOptions) {
    return 'judge'
  }

  if ((question.value.answer || []).length > 1) {
    return 'multi'
  }

  return 'single'
})

const selectedSingle = ref<string>('')
const selectedMulti = ref<string[]>([])
const essayAnswer = ref<string>('')
const submitted = ref(false)

const optionEntries = computed(() =>
  question.value.options.map((label, index) => ({
    key: optionKey(index),
    label,
  }))
)

const canSubmit = computed(() => {
  if (inferredQuestionType.value === 'essay') {
    return essayAnswer.value.trim().length > 0
  }
  if (inferredQuestionType.value === 'multi') {
    return selectedMulti.value.length > 0
  }
  return Boolean(selectedSingle.value)
})

const selectedKeys = computed(() => {
  if (inferredQuestionType.value === 'multi') {
    return selectedMulti.value
  }
  return selectedSingle.value ? [selectedSingle.value] : []
})

const answerKeys = computed(() => {
  const answers = question.value.answer || []
  if (answers.length === 0) {
    return [] as string[]
  }

  const keySet = new Set(optionEntries.value.map((item) => item.key))
  const normalizedOptionToKey = new Map(
    optionEntries.value.map((item) => [normalizeOptionText(item.label), item.key] as const)
  )

  return answers
    .map((item) => item.trim())
    .map((item) => {
      const upper = item.toUpperCase()
      if (keySet.has(upper)) {
        return upper
      }
      return normalizedOptionToKey.get(normalizeOptionText(item)) || ''
    })
    .filter(Boolean)
})

const hasAnswer = computed(() => answerKeys.value.length > 0)

const isCorrect = computed(() => {
  if (!submitted.value || !hasAnswer.value) {
    return null
  }

  const expected = [...answerKeys.value].sort()
  const actual = [...selectedKeys.value].sort()

  if (expected.length !== actual.length) {
    return false
  }

  return expected.every((item, index) => item === actual[index])
})

async function submitAnswer() {
  if (!canSubmit.value || submitLoading.value) {
    return
  }
  if (inferredQuestionType.value === 'essay') {
    selectedSingle.value = essayAnswer.value.trim()
  }
  submitted.value = true

  // 如果有 exerciseId，提交作答记录到后端
  if (props.exerciseId) {
    submitLoading.value = true
    try {
      const answer = inferredQuestionType.value === 'multi' ? selectedMulti.value : selectedSingle.value
      await submitExerciseAttempt({
        exerciseId: props.exerciseId,
        studentAnswer: answer,
      })
    } catch (e: any) {
      message.error(e?.message || '提交作答记录失败')
    } finally {
      submitLoading.value = false
    }
  }
}

const answerText = computed(() => {
  if (!hasAnswer.value) {
    return ''
  }

  const keyToLabel = new Map(optionEntries.value.map((item) => [item.key, item.label]))
  return answerKeys.value.map((key) => keyToLabel.get(key) || '').join('；')
})
</script>

<template>
  <div class="question-card">
    <div v-if="question.title" class="question-title">{{ question.title }}</div>
    <div v-if="question.content" class="question-content">{{ question.content }}</div>

    <div v-if="inferredQuestionType === 'essay'" class="question-essay">
      <a-textarea
        v-model:value="essayAnswer"
        :disabled="submitted"
        placeholder="请输入你的答案..."
        :auto-size="{ minRows: 3, maxRows: 8 }"
      />
    </div>

    <div v-else-if="optionEntries.length > 0" class="question-options">
      <a-radio-group
        v-if="inferredQuestionType === 'single' || inferredQuestionType === 'judge'"
        v-model:value="selectedSingle"
        :disabled="submitted"
      >
        <a-space direction="vertical" :size="8">
          <a-radio v-for="item in optionEntries" :key="item.key" :value="item.key">
            <span class="option-label">{{ item.label }}</span>
          </a-radio>
        </a-space>
      </a-radio-group>

      <a-checkbox-group v-else v-model:value="selectedMulti" :disabled="submitted">
        <a-space direction="vertical" :size="8">
          <a-checkbox v-for="item in optionEntries" :key="item.key" :value="item.key">
            <span class="option-label">{{ item.label }}</span>
          </a-checkbox>
        </a-space>
      </a-checkbox-group>
    </div>

    <div class="question-actions">
      <a-button
        type="primary"
        size="small"
        :disabled="submitted || !canSubmit"
        :loading="submitLoading"
        @click="submitAnswer"
        >提交答案</a-button
      >
      <span class="question-type">{{
        inferredQuestionType === 'single'
          ? '单选题'
          : inferredQuestionType === 'multi'
            ? '多选题'
            : inferredQuestionType === 'judge'
              ? '判断题'
              : '简答题'
      }}</span>
    </div>

    <div v-if="submitted" class="question-result" :class="{ correct: isCorrect === true, wrong: isCorrect === false }">
      <template v-if="hasAnswer">
        <span>{{ isCorrect ? '回答正确' : '回答错误' }}</span>
        <span class="answer-text">正确答案：{{ answerText }}</span>
      </template>
      <template v-else>
        <span>已提交答案</span>
      </template>
    </div>
  </div>
</template>

<style scoped>
@reference '#main.css';

.question-card {
  @apply w-full rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800;
  padding: 12px 16px;
}

.question-title {
  @apply mb-2 text-sm font-semibold text-gray-900 dark:text-gray-100;
}

.question-content {
  @apply mb-3 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap;
}

.question-options {
  @apply mb-3;
}

.question-essay {
  @apply mb-3;
}

.option-label {
  @apply text-sm text-gray-800 dark:text-gray-200;
}

.question-actions {
  @apply flex items-center gap-3;
}

.question-type {
  @apply text-xs text-gray-500 dark:text-gray-400;
}

.question-result {
  @apply mt-3 flex flex-col gap-1 rounded-md px-3 py-2 text-sm;
}

.question-result.correct {
  @apply bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300;
}

.question-result.wrong {
  @apply bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300;
}

.answer-text {
  @apply text-xs;
}
</style>
