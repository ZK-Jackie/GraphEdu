<template>
  <div class="teacher-dashboard">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="welcome-text">
        <h2 class="welcome-title">{{ greeting }}，{{ userStore.userName }}老师！</h2>
        <p class="welcome-sub">今天是 {{ todayStr }}，一起来查看教学概况吧</p>
      </div>
    </div>

    <!-- 统计卡片 -->
    <a-row :gutter="[16, 16]" class="mt-4">
      <a-col :xs="12" :sm="6">
        <StatCard title="我的课程" :value="`${summary.totalCourses}门`" color="blue" icon="BookOutlined" />
      </a-col>
      <a-col :xs="12" :sm="6">
        <StatCard title="总学生数" :value="summary.totalStudents" color="green" icon="UserOutlined" />
      </a-col>
      <a-col :xs="12" :sm="6">
        <StatCard
          title="今日活跃"
          :value="`${summary.todayActiveStudents}人`"
          color="orange"
          icon="LineChartOutlined"
        />
      </a-col>
      <a-col :xs="12" :sm="6">
        <StatCard
          title="平均掌握度"
          :value="summary.avgMasteryScore != null ? `${summary.avgMasteryScore}%` : '-'"
          color="purple"
          icon="TrophyOutlined"
        />
      </a-col>
    </a-row>

    <!-- 快捷工具 + 备忘录 -->
    <a-row :gutter="[16, 16]" class="mt-4 equal-height-row">
      <a-col :xs="24" :lg="14">
        <a-card :bordered="false" title="快捷工具">
          <div class="quick-tools">
            <div v-for="tool in quickTools" :key="tool.key" class="tool-item" @click="handleToolClick(tool)">
              <div class="tool-icon" :style="{ background: tool.color + '15', color: tool.color }">
                <component :is="tool.icon" />
              </div>
              <div class="tool-info">
                <div class="tool-name">{{ tool.name }}</div>
                <div class="tool-desc">{{ tool.desc }}</div>
              </div>
              <RightOutlined class="tool-arrow" />
            </div>
          </div>
        </a-card>
      </a-col>
      <a-col :xs="24" :lg="10">
        <MemoPad storage-key="teacher" />
      </a-col>
    </a-row>

    <!-- 课程概览 -->
    <div class="mt-6">
      <a-card :bordered="false" title="课程概览">
        <a-table
          v-if="courseOverview.length > 0"
          :columns="courseColumns"
          :data-source="courseOverview"
          :pagination="false"
          size="small"
          row-key="courseId"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'courseName'">
              <a @click="goToCourse(record.courseId)">{{ record.courseName }}</a>
            </template>
            <template v-if="column.key === 'avgMasteryScore'">
              <a-progress
                :percent="record.avgMasteryScore"
                size="small"
                :stroke-color="getCompletionColor(record.avgMasteryScore)"
              />
            </template>
            <template v-if="column.key === 'quizCorrectRate'">
              {{ record.quizCorrectRate != null ? `${record.quizCorrectRate}%` : '-' }}
            </template>
          </template>
        </a-table>
        <a-empty v-else description="暂无课程数据" :image-style="{ height: '40px' }" />
      </a-card>
    </div>

    <!-- 学生排名 + 互动趋势 -->
    <a-row :gutter="[16, 16]" class="mt-4 equal-height-row">
      <a-col :xs="24" :lg="14">
        <a-card :bordered="false" title="学生排名（按掌握度）">
          <a-table
            v-if="rankings.length > 0"
            :columns="rankingColumns"
            :data-source="rankings"
            :pagination="{ pageSize: 5, size: 'small' }"
            size="small"
            row-key="studentId"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'rank'">
                <span :class="getRankClass(record._rank)">
                  {{ record._rank }}
                </span>
              </template>
              <template v-if="column.key === 'masteryPercentile'">
                <a-progress
                  :percent="Math.round(record.masteryPercentile * 100)"
                  size="small"
                  :format="() => `Top ${Math.round((1 - record.masteryPercentile) * 100)}%`"
                />
              </template>
            </template>
          </a-table>
          <a-empty v-else description="暂无学生数据" :image-style="{ height: '40px' }" />
        </a-card>
      </a-col>

      <a-col :xs="24" :lg="10">
        <LearningTrendChart :daily-active="trendData" :loading="trendLoading">
          <template #extra>
            <a-space :size="8" align="center">
              <a-select
                v-model:value="selectedCourseId"
                :options="courseOptions"
                placeholder="全部课程"
                style="min-width: 120px"
                size="small"
                @change="handleCourseChange"
              />
              <a-button size="small" type="text" @click="changeWeek(-1)">
                <LeftOutlined />
              </a-button>
              <span class="week-label">{{ weekLabel }}</span>
              <a-button size="small" type="text" :disabled="isCurrentWeek" @click="changeWeek(1)">
                <RightOutlined />
              </a-button>
            </a-space>
          </template>
        </LearningTrendChart>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  PlusOutlined,
  BarChartOutlined,
  ShareAltOutlined,
  RightOutlined,
  RobotOutlined,
  LeftOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import useUserStore from '@/stores/modules/user'
import StatCard from '@/components/education/StatCard.vue'
import MemoPad from '@/components/education/MemoPad.vue'
import LearningTrendChart from '@/components/education/LearningTrendChart.vue'
import { getCompletionColor } from '@/utils/format'
import {
  getTeacherDashboardSummary,
  getTeacherDashboardCourses,
  getTeacherDashboardRankings,
  getTeacherDashboardTrendByWeek,
} from '@/api/education/dashboard'
import type {
  DailyActiveItemVO,
  TeacherDashboardCourseVO,
  TeacherDashboardRankingVO,
  TeacherDashboardSummaryVO,
} from '@/types/api/education/stats.ts'

const router = useRouter()
const userStore = useUserStore()

const summary = ref<TeacherDashboardSummaryVO>({
  totalCourses: 0,
  totalStudents: 0,
  todayActiveStudents: 0,
  avgMasteryScore: undefined,
})
const courseOverview = ref<TeacherDashboardCourseVO[]>([])
const rankings = ref<(TeacherDashboardRankingVO & { _rank: number })[]>([])
const trendData = ref<DailyActiveItemVO[]>([])
const trendLoading = ref(false)

// ==================== 课程筛选 ====================

const selectedCourseId = ref<number | undefined>(undefined)

const courseOptions = computed(() => {
  const options: { label: string; value: number | undefined }[] = [{ label: '全部课程', value: undefined }]
  for (const c of courseOverview.value) {
    options.push({ label: c.courseName, value: c.courseId })
  }
  return options
})

function handleCourseChange() {
  loadTrendData()
}

// ==================== 周导航 ====================

/** 获取某日期所在周的周一 */
function getMonday(date: Date): Date {
  const d = new Date(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  d.setHours(0, 0, 0, 0)
  return d
}

/** 格式化日期为 YYYY-MM-DD */
function formatDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/** 格式化日期为 MM-DD */
function formatShortDate(date: Date): string {
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${m}-${d}`
}

const weekStart = ref(getMonday(new Date()))

const weekLabel = computed(() => {
  const start = weekStart.value
  const end = new Date(start)
  end.setDate(end.getDate() + 6)
  return `${formatShortDate(start)} - ${formatShortDate(end)}`
})

const isCurrentWeek = computed(() => {
  const currentMonday = getMonday(new Date())
  return formatDate(weekStart.value) === formatDate(currentMonday)
})

function changeWeek(delta: number) {
  const d = new Date(weekStart.value)
  d.setDate(d.getDate() + delta * 7)
  const currentMonday = getMonday(new Date())
  if (d > currentMonday) return
  weekStart.value = d
}

/** 补全一周 7 天数据，缺失的填充为 0 */
function fillWeekData(data: DailyActiveItemVO[]): DailyActiveItemVO[] {
  const filled: DailyActiveItemVO[] = []
  for (let i = 0; i < 7; i++) {
    const d = new Date(weekStart.value)
    d.setDate(d.getDate() + i)
    const dateStr = formatShortDate(d)
    const existing = data.find((item) => item.date === dateStr)
    filled.push(existing || { date: dateStr, count: 0 })
  }
  return filled
}

// 切换周时重新加载趋势数据
watch(weekStart, () => {
  loadTrendData()
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 12) return '早上好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const todayStr = computed(() => {
  return new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
})

// 快捷工具
const quickTools = [
  {
    key: 'create-course',
    name: '创建课程',
    desc: '创建新的教学课程',
    icon: PlusOutlined,
    color: '#1890ff',
    route: '/course/create',
  },
  {
    key: 'analytics',
    name: '学生分析',
    desc: '查看学生学习数据',
    icon: BarChartOutlined,
    color: '#52c41a',
    route: '/stats/learn',
  },
  {
    key: 'knowledge-graph',
    name: 'AI 知识图谱',
    desc: '管理和构建知识图谱',
    icon: ShareAltOutlined,
    color: '#722ed1',
    route: '/course',
  },
  {
    key: 'ai-chat',
    name: 'AI 教学助手',
    desc: '智能出题和答疑辅助',
    icon: RobotOutlined,
    color: '#fa8c16',
    route: '/chat',
  },
]

// 课程表格列
const courseColumns = [
  { title: '课程名称', key: 'courseName', dataIndex: 'courseName' },
  { title: '学生数', dataIndex: 'studentCount', key: 'studentCount', width: 80 },
  { title: '平均掌握度', key: 'avgMasteryScore', width: 180 },
  { title: '答题正确率', key: 'quizCorrectRate', width: 110 },
]

// 排名表格列
const rankingColumns = [
  { title: '排名', key: 'rank', width: 60 },
  { title: '学生', dataIndex: 'studentName', key: 'studentName' },
  { title: '掌握度', key: 'masteryPercentile', width: 180 },
  { title: '评分', dataIndex: 'avgMasteryScore', key: 'avgMasteryScore', width: 80 },
]

// 排名样式
function getRankClass(rank: number): string {
  if (rank === 1) return 'rank-gold'
  if (rank === 2) return 'rank-silver'
  if (rank === 3) return 'rank-bronze'
  return 'rank-normal'
}

function handleToolClick(tool: (typeof quickTools)[number]) {
  router.push(tool.route)
}

function goToCourse(courseId: number) {
  router.push(`/course/manage/${courseId}`)
}

async function loadTrendData() {
  trendLoading.value = true
  try {
    const start = formatDate(weekStart.value)
    const end = formatDate(new Date(new Date(weekStart.value).setDate(weekStart.value.getDate() + 6)))
    const res = await getTeacherDashboardTrendByWeek(start, end, selectedCourseId.value)
    if (res.code === 200) {
      trendData.value = fillWeekData(res.data || [])
    }
  } catch (e) {
    console.error('加载趋势数据失败:', e)
  } finally {
    trendLoading.value = false
  }
}

async function loadData() {
  try {
    const [summaryRes, coursesRes, rankingsRes] = await Promise.allSettled([
      getTeacherDashboardSummary(),
      getTeacherDashboardCourses(),
      getTeacherDashboardRankings(10),
    ])

    if (summaryRes.status === 'fulfilled' && summaryRes.value.code === 200) {
      summary.value = summaryRes.value.data
    }

    if (coursesRes.status === 'fulfilled' && coursesRes.value.code === 200) {
      courseOverview.value = coursesRes.value.data || []
    }

    if (rankingsRes.status === 'fulfilled' && rankingsRes.value.code === 200) {
      rankings.value = (rankingsRes.value.data || []).map((r, i) => ({ ...r, _rank: i + 1 }))
    }
  } catch (error: any) {
    console.error('加载教师仪表盘数据失败:', error)
    message.error(error.message || '加载数据失败')
  }
}

onMounted(() => {
  loadData()
  loadTrendData()
})
</script>

<style scoped>
@reference '#main.css';

.teacher-dashboard {
  @apply p-6 max-w-7xl mx-auto;
}

/* 欢迎横幅 */
.welcome-banner {
  @apply flex items-center justify-between p-6 rounded-xl;
  background: linear-gradient(135deg, #059669 0%, #34d399 100%);
  color: white;
}

html.dark .welcome-banner {
  background: linear-gradient(135deg, #047857 0%, #1c7a4a 100%);
}

.welcome-title {
  @apply text-2xl font-bold m-0;
}

.welcome-sub {
  @apply text-sm opacity-90 mt-2 m-0;
}

/* 周导航标签 */
.week-label {
  display: inline-block;
  min-width: 120px;
  text-align: center;
  font-weight: 500;
  font-size: 13px;
  color: var(--ge-text-secondary);
}

/* 快捷工具 */
.quick-tools {
  @apply flex flex-col gap-2;
}

.tool-item {
  @apply flex items-center gap-3 p-3 rounded-lg border border-gray-100 dark:border-gray-700 cursor-pointer transition-all hover:shadow-md hover:border-green-200;
}

.tool-icon {
  @apply flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center text-lg;
}

.tool-info {
  @apply flex-1 min-w-0;
}

.tool-name {
  @apply font-medium text-sm text-gray-800 dark:text-gray-100;
}

.tool-desc {
  @apply text-xs text-gray-400 dark:text-gray-500 mt-0.5;
}

.tool-arrow {
  @apply text-gray-300 dark:text-gray-600;
}

/* 排名样式 */
.rank-gold {
  @apply inline-flex items-center justify-center w-6 h-6 rounded-full bg-yellow-400 text-white text-xs font-bold;
}

.rank-silver {
  @apply inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-300 text-white text-xs font-bold;
}

.rank-bronze {
  @apply inline-flex items-center justify-center w-6 h-6 rounded-full bg-orange-400 text-white text-xs font-bold;
}

.rank-normal {
  @apply text-sm text-gray-500;
}

/* 等高行：让同一行卡片等高，右侧卡片内容溢出滚动 */
.equal-height-row :deep(.ant-col) {
  display: flex;
}

.equal-height-row :deep(.ant-card) {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.equal-height-row :deep(.ant-card-body) {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.equal-height-row :deep(.memo-list) {
  max-height: none;
}
</style>
