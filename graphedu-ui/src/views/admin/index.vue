<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  UserOutlined,
  TeamOutlined,
  SolutionOutlined,
  BookOutlined,
  ApartmentOutlined,
  LoginOutlined,
} from '@ant-design/icons-vue'
import { getAdminDashboardOverview } from '@/api/system/adminDashboard'
import { getOperationLogList } from '@/api/system/log'
import type { AdminDashboardSummaryVO } from '@/types/api/system/adminDashboard'
import type { OperLogListVO } from '@/types/api/system/log'
import { useTime } from '@/composables/useTime'

const { t } = useI18n()
const { formatUtcTime } = useTime()

const loading = ref(true)
const overview = ref<AdminDashboardSummaryVO>({
  totalUsers: 0,
  totalStudents: 0,
  totalTeachers: 0,
  totalCourses: 0,
  totalKnowledgeGraphs: 0,
  todayLoginUsers: 0,
})

const recentLogs = ref<OperLogListVO[]>([])

const statCards = computed(() => [
  {
    title: t('system.dashboard.totalUsers'),
    value: overview.value.totalUsers,
    icon: UserOutlined,
    color: '#1890ff',
  },
  {
    title: t('system.dashboard.totalStudents'),
    value: overview.value.totalStudents,
    icon: TeamOutlined,
    color: '#52c41a',
  },
  {
    title: t('system.dashboard.totalTeachers'),
    value: overview.value.totalTeachers,
    icon: SolutionOutlined,
    color: '#722ed1',
  },
  {
    title: t('system.dashboard.totalCourses'),
    value: overview.value.totalCourses,
    icon: BookOutlined,
    color: '#fa8c16',
  },
  {
    title: t('system.dashboard.totalKnowledgeGraphs'),
    value: overview.value.totalKnowledgeGraphs,
    icon: ApartmentOutlined,
    color: '#13c2c2',
  },
  {
    title: t('system.dashboard.todayLoginUsers'),
    value: overview.value.todayLoginUsers,
    icon: LoginOutlined,
    color: '#eb2f96',
  },
])

const logColumns = [
  { title: t('system.dashboard.module'), dataIndex: 'title', width: 160 },
  { title: t('system.dashboard.businessType'), dataIndex: 'businessType', width: 100 },
  { title: t('system.dashboard.operator'), dataIndex: 'operName', width: 120 },
  { title: t('system.dashboard.operTime'), dataIndex: 'operTime', width: 180 },
  { title: t('system.dashboard.costTime'), dataIndex: 'costTime', width: 100 },
  { title: t('system.dashboard.status'), dataIndex: 'status', width: 80 },
]

const businessTypeMap: Record<number, string> = {
  0: t('system.log.operation.operateTypeOther'),
  1: t('system.log.operation.operateTypeInsert'),
  2: t('system.log.operation.operateTypeUpdate'),
  3: t('system.log.operation.operateTypeDelete'),
  4: t('system.log.operation.operateTypeGrant'),
  5: t('system.log.operation.operateTypeExport'),
  6: t('system.log.operation.operateTypeImport'),
  7: t('system.log.operation.operateTypeForce'),
  8: t('system.log.operation.operateTypeGenCode'),
  9: t('system.log.operation.operateTypeClean'),
}

function getBusinessTypeLabel(type: number): string {
  return businessTypeMap[type] ?? String(type)
}

async function fetchData() {
  loading.value = true
  try {
    const [overviewRes, logRes] = await Promise.all([
      getAdminDashboardOverview(),
      getOperationLogList({ page: 1, size: 10 }),
    ])
    if (overviewRes.data) {
      overview.value = overviewRes.data
    }
    if (logRes.data?.rows) {
      recentLogs.value = logRes.data.rows
    }
  } catch {
    // silently fail — dashboard is non-critical
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="dashboard">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">{{ t('system.dashboard.title') }}</h1>
      <p class="page-subtitle">{{ t('system.dashboard.welcome') }}</p>
    </div>

    <!-- 统计卡片 -->
    <a-spin :spinning="loading">
      <div class="statistics-grid">
        <a-card v-for="card in statCards" :key="card.title" class="stat-card" :body-style="{ padding: '20px 24px' }">
          <div class="stat-content">
            <div class="stat-info">
              <div class="stat-title">{{ card.title }}</div>
              <div class="stat-value">{{ card.value.toLocaleString() }}</div>
            </div>
            <div class="stat-icon" :style="{ background: card.color + '20', color: card.color }">
              <component :is="card.icon" :style="{ fontSize: '28px' }" />
            </div>
          </div>
        </a-card>
      </div>
    </a-spin>

    <!-- 最近操作日志 -->
    <a-card :title="t('system.dashboard.recentActivity')" :body-style="{ padding: '0' }" style="margin-top: 16px">
      <a-table
        :columns="logColumns"
        :data-source="recentLogs"
        :loading="loading"
        :pagination="false"
        row-key="operId"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'title'">
            {{ record.title }}
          </template>
          <template v-else-if="column.dataIndex === 'businessType'">
            {{ getBusinessTypeLabel(record.businessType) }}
          </template>
          <template v-else-if="column.dataIndex === 'operName'">
            {{ record.operName }}
          </template>
          <template v-else-if="column.dataIndex === 'operTime'">
            {{ formatUtcTime(record.operTime) }}
          </template>
          <template v-else-if="column.dataIndex === 'costTime'">
            {{ record.costTime }} {{ t('system.dashboard.ms') }}
          </template>
          <template v-else-if="column.dataIndex === 'status'">
            <a-tag :color="record.status === 0 ? 'success' : 'error'">
              {{ record.status === 0 ? t('system.job.success') : t('system.job.failed') }}
            </a-tag>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<style scoped>
@reference "#main.css";

.dashboard {
  padding: 24px;
  min-height: calc(100vh - 64px);
  background: var(--ge-bg-page);
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: var(--ge-text-primary);
}

.page-subtitle {
  color: var(--ge-text-secondary);
  margin: 8px 0 0 0;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.stat-card {
  border-radius: 8px;
  box-shadow: var(--ge-shadow);
  transition: all 0.3s;
}

.stat-card:hover {
  box-shadow: var(--ge-shadow-medium);
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-info {
  flex: 1;
}

.stat-title {
  font-size: 14px;
  color: var(--ge-text-secondary);
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--ge-text-primary);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 768px) {
  .dashboard {
    padding: 16px;
  }

  .statistics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
