<template>
  <div>
    <!-- 顶部统计卡片 -->
    <a-row :gutter="16" class="mb-4">
      <a-col :span="6">
        <a-card size="small">
          <a-statistic :title="t('education.chapter.totalChapters')" :value="data?.totalChapters ?? 0" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic :title="t('education.chapter.completedChapters')" :value="data?.completedChapters ?? 0" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic :title="t('education.analytics.completionRate')" :value="completionRate" suffix="%" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic
            :title="t('education.student.totalStudyTime')"
            :value="formatDuration(data?.totalStudySeconds ?? 0)"
          />
        </a-card>
      </a-col>
    </a-row>

    <!-- 章节学习表格 -->
    <a-table
      :columns="columns"
      :data-source="data?.chapters ?? []"
      :loading="loading"
      :pagination="false"
      row-key="chapterId"
      :expandable="{ expandedRowKeys, onExpand: handleExpand }"
      size="small"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'completionRate'">
          <a-progress :percent="record.completionRate" :size="'small'" :stroke-width="6" />
        </template>
        <template v-else-if="column.key === 'quizCorrectRate'">
          <span v-if="record.quizCorrectRate !== null && record.quizCorrectRate !== undefined">
            {{ record.quizCorrectRate }}%
          </span>
          <span v-else class="text-gray-400">-</span>
        </template>
        <template v-else-if="column.key === 'avgMasteryScore'">
          <a-tag
            v-if="record.avgMasteryScore !== null && record.avgMasteryScore !== undefined"
            :color="getMasteryColor(record.avgMasteryScore)"
          >
            {{ record.avgMasteryScore }}
          </a-tag>
          <span v-else class="text-gray-400">-</span>
        </template>
        <template v-else-if="column.key === 'totalStudySeconds'">
          {{ formatDuration(record.totalStudySeconds) }}
        </template>
        <template v-else-if="column.key === 'lastStudyTime'">
          {{ parseTime(record.lastStudyTime) || '-' }}
        </template>
      </template>

      <!-- 展开行内容 -->
      <template #expandedRowRender="{ record }">
        <div class="pl-12 py-2">
          <a-spin v-if="detailLoading[record.chapterId]" :tip="t('common.loading')" size="small">
            <div class="h-20" />
          </a-spin>
          <a-tabs
            v-else
            v-model:activeKey="activeDetailTab[record.chapterId]"
            size="small"
            @change="(key: string | number) => handleDetailTabChange(record.chapterId, String(key))"
          >
            <a-tab-pane key="resources" :tab="t('education.analytics.resourceReading')">
              <a-table
                v-if="detailCache[record.chapterId]?.resources"
                :columns="resourceColumns"
                :data-source="detailCache[record.chapterId]!.resources"
                :pagination="false"
                row-key="progressId"
                size="small"
              >
                <template #bodyCell="{ column: col, record: row }">
                  <template v-if="col.key === 'completionRate'">
                    <a-progress :percent="row.completionRate" :size="'small'" :stroke-width="4" />
                  </template>
                  <template v-else-if="col.key === 'totalDuration'">
                    {{ formatDuration(row.totalDuration) }}
                  </template>
                </template>
              </a-table>
              <a-empty v-else :description="t('common.noData')" />
            </a-tab-pane>
            <a-tab-pane key="exercises" :tab="t('education.analytics.exerciseRecords')">
              <a-table
                v-if="detailCache[record.chapterId]?.exercises"
                :columns="exerciseColumns"
                :data-source="detailCache[record.chapterId]!.exercises"
                :pagination="false"
                row-key="attemptId"
                size="small"
              >
                <template #bodyCell="{ column: col, record: row }">
                  <template v-if="col.key === 'isCorrect'">
                    <a-tag :color="row.isCorrect ? 'success' : 'error'">
                      {{ row.isCorrect ? t('common.correct') : t('common.incorrect') }}
                    </a-tag>
                  </template>
                  <template v-else-if="col.key === 'timeSpent'">
                    {{ row.timeSpent ? `${row.timeSpent}s` : '-' }}
                  </template>
                </template>
              </a-table>
              <a-empty v-else :description="t('common.noData')" />
            </a-tab-pane>
            <a-tab-pane key="mastery" :tab="t('education.analytics.knowledgeMastery')">
              <a-table
                v-if="detailCache[record.chapterId]?.mastery"
                :columns="masteryColumns"
                :data-source="detailCache[record.chapterId]!.mastery"
                :pagination="false"
                row-key="masteryId"
                size="small"
              >
                <template #bodyCell="{ column: col, record: row }">
                  <template v-if="col.key === 'masteryScore'">
                    <a-tag
                      v-if="row.masteryScore !== null && row.masteryScore !== undefined"
                      :color="getMasteryColor(row.masteryScore)"
                    >
                      {{ row.masteryScore }}
                    </a-tag>
                    <span v-else>-</span>
                  </template>
                  <template v-else-if="col.key === 'masteryLevel'">
                    <a-tag v-if="row.masteryLevel" :color="getLevelColor(row.masteryLevel)">
                      {{ row.masteryLevel }}
                    </a-tag>
                    <span v-else>-</span>
                  </template>
                </template>
              </a-table>
              <a-empty v-else :description="t('common.noData')" />
            </a-tab-pane>
          </a-tabs>
        </div>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { getStudentChapterLearning, getStudentChapterDetail } from '@/api/education/teach_analytics'
import { parseTime } from '@/utils/common.ts'
import type {
  StudentChapterDetailResultVO,
  StudentChapterLearningResultVO,
  StudentChapterResourceDetailVO,
} from '@/types/api/education/stats.ts'
import type { StudentChapterExerciseDetailVO } from '@/types/api/education/courseExercise.ts'
import type { StudentChapterMasteryDetailVO } from '@/types/api/education/mastery.ts'

const { t } = useI18n()

interface Props {
  courseId: number
  studentId: number | undefined
}

const props = defineProps<Props>()

const loading = ref(false)
const data = ref<StudentChapterLearningResultVO>()

// 展开行状态
const expandedRowKeys = ref<number[]>([])
const detailLoading = reactive<Record<number, boolean>>({})
const detailCache = reactive<Record<number, Record<string, unknown[]>>>({})
const activeDetailTab = reactive<Record<number, string>>({})

const completionRate = computed(() => {
  if (!data.value || data.value.totalChapters === 0) return 0
  return Math.round((data.value.completedChapters / data.value.totalChapters) * 100)
})

const columns = computed(() => [
  {
    title: t('education.chapter.chapterName'),
    dataIndex: 'chapterName',
    key: 'chapterName',
    width: 200,
  },
  {
    title: t('education.analytics.completionRate'),
    key: 'completionRate',
    width: 120,
    align: 'center' as const,
  },
  {
    title: t('education.analytics.quizCorrectRate'),
    key: 'quizCorrectRate',
    width: 120,
    align: 'center' as const,
  },
  {
    title: t('education.analytics.masteryScore'),
    key: 'avgMasteryScore',
    width: 120,
    align: 'center' as const,
  },
  {
    title: t('education.analytics.studyTime'),
    key: 'totalStudySeconds',
    width: 100,
    align: 'center' as const,
  },
  {
    title: t('common.lastStudyTime'),
    key: 'lastStudyTime',
    width: 160,
  },
])

const resourceColumns = computed(() => [
  {
    title: t('education.resource.resourceName'),
    dataIndex: 'resourceName',
    key: 'resourceName',
    width: 200,
  },
  {
    title: t('education.resource.resourceType'),
    dataIndex: 'resourceType',
    key: 'resourceType',
    width: 80,
  },
  {
    title: t('education.analytics.completionRate'),
    key: 'completionRate',
    width: 120,
  },
  {
    title: t('education.analytics.viewCount'),
    dataIndex: 'viewCount',
    key: 'viewCount',
    width: 80,
  },
  {
    title: t('education.analytics.studyTime'),
    key: 'totalDuration',
    width: 100,
  },
])

const exerciseColumns = computed(() => [
  { title: 'ID', dataIndex: 'exerciseId', key: 'exerciseId', width: 80 },
  { title: t('education.analytics.isCorrect'), key: 'isCorrect', width: 100 },
  { title: t('education.analytics.timeSpent'), key: 'timeSpent', width: 100 },
  {
    title: t('education.analytics.attemptTime'),
    dataIndex: 'attemptTime',
    key: 'attemptTime',
    width: 160,
  },
])

const masteryColumns = computed(() => [
  {
    title: t('education.knowledgePoint.name'),
    dataIndex: 'nodeTitle',
    key: 'nodeTitle',
    width: 200,
  },
  {
    title: t('education.analytics.masteryScore'),
    key: 'masteryScore',
    width: 120,
  },
  {
    title: t('education.analytics.masteryLevel'),
    key: 'masteryLevel',
    width: 100,
  },
  {
    title: t('education.analytics.assessTime'),
    dataIndex: 'assessedAt',
    key: 'assessedAt',
    width: 160,
  },
])

const formatDuration = (seconds: number) => {
  if (!seconds) return '-'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m`
  return `${seconds}s`
}

const getMasteryColor = (score: number) => {
  if (score >= 80) return 'green'
  if (score >= 60) return 'blue'
  if (score >= 40) return 'orange'
  return 'red'
}

const getLevelColor = (level: string) => {
  switch (level) {
    case 'high':
      return 'green'
    case 'medium':
      return 'blue'
    case 'low':
      return 'orange'
    default:
      return 'default'
  }
}

const handleExpand = async (expanded: boolean, record: { chapterId: number }) => {
  if (expanded) {
    expandedRowKeys.value = [...expandedRowKeys.value, record.chapterId]
    if (!detailCache[record.chapterId]) {
      activeDetailTab[record.chapterId] = 'resources'
      await loadChapterDetail(record.chapterId, 'resources')
    }
  } else {
    expandedRowKeys.value = expandedRowKeys.value.filter((k) => k !== record.chapterId)
  }
}

const handleDetailTabChange = async (chapterId: number, tabKey: string) => {
  if (!detailCache[chapterId]?.[tabKey]) {
    await loadChapterDetail(chapterId, tabKey)
  }
}

const loadChapterDetail = async (chapterId: number, detailType: string) => {
  if (!props.studentId || !props.courseId) return
  detailLoading[chapterId] = true
  try {
    const res = await getStudentChapterDetail(
      props.courseId,
      props.studentId,
      chapterId,
      detailType as 'resources' | 'exercises' | 'mastery'
    )
    if (res.code === 200) {
      if (!detailCache[chapterId]) detailCache[chapterId] = {}
      detailCache[chapterId][detailType] = res.data.items || []
    }
  } catch (_e) {
    message.error(t('common.loadFailed'))
  } finally {
    detailLoading[chapterId] = false
  }
}

const loadData = async () => {
  if (!props.studentId || !props.courseId) return
  loading.value = true
  try {
    const res = await getStudentChapterLearning(props.courseId, props.studentId)
    if (res.code === 200) {
      data.value = res.data
    }
  } catch (_e) {
    message.error(t('common.loadFailed'))
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.studentId, props.courseId],
  () => {
    // 重置展开状态
    expandedRowKeys.value = []
    Object.keys(detailCache).forEach((k) => delete detailCache[Number(k)])
    Object.keys(detailLoading).forEach((k) => delete detailLoading[Number(k)])
    Object.keys(activeDetailTab).forEach((k) => delete activeDetailTab[Number(k)])
    loadData()
  },
  { immediate: true }
)
</script>
