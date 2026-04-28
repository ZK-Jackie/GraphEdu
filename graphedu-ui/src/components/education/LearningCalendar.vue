<template>
  <a-card title="学习日历" :bordered="false">
    <template #extra>
      <a-space :size="4" align="center">
        <a-button size="small" type="text" @click="changeYear(-1)">
          <LeftOutlined />
        </a-button>
        <span class="year-label">{{ selectedYear }}</span>
        <a-button size="small" type="text" :disabled="selectedYear >= currentYear" @click="changeYear(1)">
          <RightOutlined />
        </a-button>
      </a-space>
    </template>
    <a-spin :spinning="loading">
      <div ref="chartRef" class="calendar-chart" />
    </a-spin>
  </a-card>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { LeftOutlined, RightOutlined } from '@ant-design/icons-vue'
import { echarts } from '@/plugins/echarts'
import { getStudentDashboardCalendar } from '@/api/education/dashboard'
import useAppStore from '@/stores/modules/app'
import type { DashboardCalendarItemVO } from '@/types/api/education/stats.ts'

const chartRef = ref<HTMLElement | null>(null)
let chartInstance: ReturnType<typeof echarts.init> | null = null

const currentYear = new Date().getFullYear()
const selectedYear = ref(currentYear)
const calendarData = ref<DashboardCalendarItemVO[]>([])
const loading = ref(false)

/** 判断当前是否暗色模式 */
const appStore = useAppStore()
const { darkMode } = storeToRefs(appStore)

const option = computed(() => {
  const year = selectedYear.value
  const data = calendarData.value || []
  const heatmapData = data.map((d) => [d.date, d.minutes] as [string, number])
  const isDark = darkMode.value

  return {
    backgroundColor: 'transparent',
    tooltip: {
      formatter: (params: any) => {
        const date = params.value?.[0] || ''
        const val = params.value?.[1] ?? 0
        return `${date}<br/>学习 <b>${val}</b> 分钟`
      },
    },
    visualMap: {
      min: 0,
      max: 120,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      inRange: {
        color: isDark
          ? ['#1f1f1f', '#0d429a', '#1a5cc8', '#3b7cd4', '#5598eb']
          : ['#ebedf0', '#9be9a8', '#40c463', '#39d353', '#26a641'],
      },
      text: ['多', '少'],
      showLabel: true,
      textStyle: { color: isDark ? 'rgba(255,255,255,0.65)' : '#666' },
    },
    calendar: {
      top: 40,
      left: 40,
      right: 40,
      bottom: 40,
      range: year,
      cellSize: ['auto', 16],
      splitLine: {
        show: true,
        lineStyle: { color: isDark ? '#3a3a3a' : '#d9d9d9', width: 1, type: 'solid' as const },
      },
      itemStyle: {
        borderWidth: isDark ? 1 : 2,
        borderColor: isDark ? '#333' : '#e8e8e8',
        color: isDark ? '#2a2a2a' : '#f5f5f5',
      },
      yearLabel: { show: false },
      monthLabel: {
        nameMap: 'ZH',
        fontSize: 12,
        color: isDark ? 'rgba(255,255,255,0.65)' : '#666',
      },
      dayLabel: {
        firstDay: 1,
        color: isDark ? 'rgba(255,255,255,0.45)' : '#999',
        fontSize: 10,
      },
    },
    series: [
      {
        type: 'heatmap',
        coordinateSystem: 'calendar',
        data: heatmapData,
        itemStyle: {
          borderRadius: 2,
        },
      },
    ],
  }
})

async function fetchData() {
  loading.value = true
  try {
    const res = await getStudentDashboardCalendar(selectedYear.value)
    if (res.code === 200) {
      calendarData.value = res.data || []
    }
  } catch (e) {
    console.error('加载日历数据失败:', e)
  } finally {
    loading.value = false
    // 数据加载完成后刷新图表
    await nextTick()
    ensureChart()
  }
}

function changeYear(delta: number) {
  const newYear = selectedYear.value + delta
  if (newYear > currentYear) return
  selectedYear.value = newYear
}

function ensureChart() {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  chartInstance.setOption(option.value, true)
  chartInstance.resize()
}

function handleResize() {
  chartInstance?.resize()
}

watch(selectedYear, () => {
  fetchData()
})

// 暗色模式变化时重绘图表
watch(darkMode, () => {
  nextTick(() => ensureChart())
})

onMounted(() => {
  fetchData()
  // 初始渲染空日历网格（不等数据）
  nextTick(() => ensureChart())
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped>
.calendar-chart {
  width: 100%;
  height: 220px;
}

.year-label {
  display: inline-block;
  min-width: 36px;
  text-align: center;
  font-weight: 500;
  font-size: 14px;
  color: var(--ge-text-primary);
}
</style>
