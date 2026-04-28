<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import type { TablePaginationConfig } from 'ant-design-vue'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  FileSearchOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue'
import { getExerciseAttemptDetail, getExerciseAttemptList } from '@/api/education/exerciseAttempt.ts'
import type { ExerciseAttemptQueryDTO, ExerciseAttemptVO } from '@/types/api/education/courseExercise.ts'
import { parseTime } from '@/utils/common.ts'

const route = useRoute()
const courseId = computed(() => Number(route.params.courseId))

// ── 表格状态 ──
const loading = ref(false)
const rows = ref<ExerciseAttemptVO[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(10)

// ── 筛选状态 ──
const filterCorrect = ref<string | undefined>(undefined)

// ── 详情弹窗 ──
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailData = ref<ExerciseAttemptVO | null>(null)

const pagination = computed<TablePaginationConfig>(() => ({
  current: page.value,
  pageSize: size.value,
  total: total.value,
  showSizeChanger: true,
  showTotal: (v: number) => `共 ${v} 条`,
}))

/** 统计卡片数据（基于全量记录，非当前页） */
const statTotal = ref(0)
const statCorrect = ref(0)
const statGraded = ref(0)
const statAvgTime = ref(0)

async function loadStats() {
  if (!courseId.value || isNaN(courseId.value)) return
  try {
    // 取全部记录来算统计（不分页）
    const res = await getExerciseAttemptList({ courseId: courseId.value, page: 1, size: 1 })
    if (res.code === 200) {
      statTotal.value = res.data?.total ?? 0
    }
  } catch {
    // 静默失败
  }
}

async function loadData() {
  if (!courseId.value || isNaN(courseId.value)) return
  loading.value = true

  const params: ExerciseAttemptQueryDTO = {
    courseId: courseId.value,
    page: page.value,
    size: size.value,
  }

  if (filterCorrect.value === 'true') {
    params.isCorrect = true
  } else if (filterCorrect.value === 'false') {
    params.isCorrect = false
  }

  try {
    const res = await getExerciseAttemptList(params)
    if (res.code === 200) {
      rows.value = res.data?.rows ?? []
      total.value = res.data?.total ?? 0

      // 从当前页数据计算统计
      const graded = rows.value.filter((r) => r.isCorrect !== null)
      statCorrect.value = graded.filter((r) => r.isCorrect === true).length
      statGraded.value = graded.length
      const times = rows.value.filter((r) => r.timeSpent != null).map((r) => r.timeSpent as number)
      statAvgTime.value = times.length > 0 ? Math.round(times.reduce((a, b) => a + b, 0) / times.length) : 0
    }
  } catch {
    message.error('加载答题记录失败')
  } finally {
    loading.value = false
  }
}

function handleTableChange(pager: TablePaginationConfig) {
  page.value = pager.current || 1
  size.value = pager.pageSize || 10
  loadData()
}

function handleSearch() {
  page.value = 1
  loadData()
}

function handleReset() {
  filterCorrect.value = undefined
  page.value = 1
  loadData()
}

async function handleViewDetail(record: ExerciseAttemptVO) {
  detailVisible.value = true
  detailLoading.value = true
  detailData.value = null
  try {
    const res = await getExerciseAttemptDetail(record.attemptId)
    if (res.code === 200) {
      detailData.value = res.data
    }
  } catch {
    message.error('加载详情失败')
  } finally {
    detailLoading.value = false
  }
}

function formatTimeSpent(seconds: number | null | undefined): string {
  if (seconds == null) return '-'
  if (seconds < 60) return `${seconds}秒`
  const min = Math.floor(seconds / 60)
  const sec = seconds % 60
  return sec > 0 ? `${min}分${sec}秒` : `${min}分钟`
}

function formatAnswer(answer: string[] | string | null | undefined): string {
  if (answer == null) return '-'
  if (Array.isArray(answer)) return answer.join(', ')
  return String(answer)
}

onMounted(() => {
  loadData()
  loadStats()
})
</script>

<template>
  <div class="exercise-record-page">
    <!-- 统计概览 -->
    <a-row :gutter="[16, 16]" class="mb-4">
      <a-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-label">总答题数</div>
          <div class="stat-value text-blue-600">{{ total }}</div>
        </div>
      </a-col>
      <a-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-label">正确数</div>
          <div class="stat-value text-green-600">{{ statCorrect }}</div>
        </div>
      </a-col>
      <a-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-label">正确率</div>
          <div class="stat-value text-orange-600">
            {{ statGraded > 0 ? Math.round((statCorrect / statGraded) * 100) : 0 }}%
          </div>
        </div>
      </a-col>
      <a-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-label">平均用时</div>
          <div class="stat-value text-purple-600">{{ formatTimeSpent(statAvgTime) }}</div>
        </div>
      </a-col>
    </a-row>

    <!-- 筛选区 -->
    <div class="filter-bar mb-4">
      <a-space>
        <a-select v-model:value="filterCorrect" placeholder="答题结果" allow-clear style="width: 140px">
          <a-select-option value="true">正确</a-select-option>
          <a-select-option value="false">错误</a-select-option>
        </a-select>
        <a-button type="primary" @click="handleSearch">
          <template #icon><SearchOutlined /></template>
          查询
        </a-button>
        <a-button @click="handleReset">重置</a-button>
        <a-button @click="loadData">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
      </a-space>
    </div>

    <!-- 数据表格 -->
    <a-table
      :data-source="rows"
      :loading="loading"
      row-key="attemptId"
      :pagination="pagination"
      size="small"
      @change="handleTableChange"
    >
      <a-table-column key="attemptId" title="记录ID" data-index="attemptId" :width="88" />
      <a-table-column key="exerciseId" title="习题ID" data-index="exerciseId" :width="88" />
      <a-table-column key="studentAnswer" title="学生答案" :ellipsis="true" :width="180">
        <template #default="{ record }">
          {{ formatAnswer(record.studentAnswer) }}
        </template>
      </a-table-column>
      <a-table-column key="isCorrect" title="结果" :width="100" align="center">
        <template #default="{ record }">
          <a-tag v-if="record.isCorrect === true" color="success">
            <template #icon><CheckCircleOutlined /></template>
            正确
          </a-tag>
          <a-tag v-else-if="record.isCorrect === false" color="error">
            <template #icon><CloseCircleOutlined /></template>
            错误
          </a-tag>
          <a-tag v-else color="default">待批改</a-tag>
        </template>
      </a-table-column>
      <a-table-column key="timeSpent" title="用时" :width="110" align="center">
        <template #default="{ record }">
          <span class="inline-flex items-center gap-1">
            <ClockCircleOutlined class="text-gray-400" />
            {{ formatTimeSpent(record.timeSpent) }}
          </span>
        </template>
      </a-table-column>
      <a-table-column key="attemptTime" title="作答时间" :width="180">
        <template #default="{ record }">
          {{ parseTime(record.attemptTime) || '-' }}
        </template>
      </a-table-column>
      <a-table-column key="action" title="操作" :width="100" align="center" fixed="right">
        <template #default="{ record }">
          <a-button type="link" size="small" @click="handleViewDetail(record)">
            <template #icon><FileSearchOutlined /></template>
            详情
          </a-button>
        </template>
      </a-table-column>
    </a-table>

    <!-- 详情弹窗 -->
    <a-modal v-model:open="detailVisible" title="作答详情" :footer="null" width="600px">
      <a-spin :spinning="detailLoading">
        <template v-if="detailData">
          <a-descriptions :column="1" bordered size="small">
            <a-descriptions-item label="记录ID">{{ detailData.attemptId }}</a-descriptions-item>
            <a-descriptions-item label="习题ID">{{ detailData.exerciseId }}</a-descriptions-item>
            <a-descriptions-item label="学生答案">
              {{ formatAnswer(detailData.studentAnswer) }}
            </a-descriptions-item>
            <a-descriptions-item label="答题结果">
              <a-tag v-if="detailData.isCorrect === true" color="success">正确</a-tag>
              <a-tag v-else-if="detailData.isCorrect === false" color="error">错误</a-tag>
              <a-tag v-else color="default">待批改</a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="用时">
              {{ formatTimeSpent(detailData.timeSpent) }}
            </a-descriptions-item>
            <a-descriptions-item label="作答时间">{{ parseTime(detailData.attemptTime) || '-' }}</a-descriptions-item>
          </a-descriptions>
        </template>
        <a-empty v-else description="暂无数据" />
      </a-spin>
    </a-modal>
  </div>
</template>

<style scoped>
@reference '#main.css';

.exercise-record-page {
  @apply p-4;
}

.stat-card {
  @apply flex flex-col items-center gap-1 rounded-lg p-4 shadow-sm;
  background: var(--ge-bg-container);
}

.stat-label {
  @apply text-sm;
  color: var(--ge-text-secondary);
}

.stat-value {
  @apply text-2xl font-bold;
}

.filter-bar {
  @apply flex items-center;
}
</style>
