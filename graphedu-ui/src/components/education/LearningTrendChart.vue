<template>
  <a-card title="学习活跃度趋势" :bordered="false" :body-style="{ padding: '12px' }">
    <template #extra>
      <slot name="extra" />
    </template>
    <div class="chart-wrapper">
      <div ref="chartRef" class="chart-container" />
      <div v-if="loading" class="chart-overlay">
        <a-skeleton active :paragraph="{ rows: 4 }" />
      </div>
      <div v-if="!loading && chartData.length === 0" class="chart-overlay">
        <a-empty description="暂无学习数据" />
      </div>
    </div>
  </a-card>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { echarts } from '@/plugins/echarts'
import type { DailyActiveItemVO, DailyActiveMinutesVO } from '@/types/api/education/stats.ts'

type DailyActiveData = DailyActiveItemVO[] | DailyActiveMinutesVO[]

interface Props {
  dailyActive: DailyActiveData
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

const chartRef = ref<HTMLElement | null>(null)
let chartInstance: ReturnType<typeof echarts.init> | null = null

const chartData = computed(() => props.dailyActive || [])

/** 判断数据类型：包含 activeMinutes 字段则为时长数据，否则为人数数据 */
function isMinutesData(data: DailyActiveData): data is DailyActiveMinutesVO[] {
  return data.length > 0 && data[0] != null && 'activeMinutes' in data[0]
}

const option = computed(() => {
  const data = chartData.value
  if (!data.length) return null

  const useMinutes = isMinutesData(data)
  const values = data.map((d) =>
    useMinutes ? (d as DailyActiveMinutesVO).activeMinutes : (d as DailyActiveItemVO).count
  )
  const maxVal = Math.max(...values, useMinutes ? 60 : 10)
  const unit = useMinutes ? '分钟' : '人'
  const yAxisName = useMinutes ? '分钟' : '活跃人数'

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const d = params[0] || params
        return `${d.name}<br/>学习 <b>${d.value}</b> ${unit}`
      },
    },
    grid: {
      left: 40,
      right: 16,
      top: 16,
      bottom: 32,
    },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.date),
      axisLabel: {
        fontSize: 11,
        color: '#999',
      },
      axisTick: {
        alignWithLabel: true,
      },
    },
    yAxis: {
      type: 'value',
      name: yAxisName,
      nameTextStyle: { fontSize: 11, color: '#999' },
      splitLine: { lineStyle: { type: 'dashed' as const } },
    },
    series: [
      {
        type: 'bar',
        data: values,
        barMaxWidth: 20,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: (params: any) => {
            const v = params.value as number
            if (useMinutes) {
              if (v >= 60) return '#52c41a'
              if (v >= 30) return '#1890ff'
              return '#faad14'
            }
            if (v >= maxVal * 0.6) return '#52c41a'
            if (v >= maxVal * 0.3) return '#1890ff'
            return '#faad14'
          },
        },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.15)' },
        },
      },
    ],
  }
})

function ensureChart() {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  if (option.value) {
    chartInstance.setOption(option.value, true)
    chartInstance.resize()
  }
}

function handleResize() {
  chartInstance?.resize()
}

watch(option, async () => {
  await nextTick()
  ensureChart()
})

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped>
.chart-wrapper {
  position: relative;
}
.chart-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  z-index: 1;
  padding: 32px 0;
}
.chart-container {
  width: 100%;
  height: 280px;
}
</style>
