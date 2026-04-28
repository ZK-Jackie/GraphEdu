<template>
  <a-card
    :bordered="false"
    :class="['stat-card', { 'stat-card--loading': loading }, `stat-card--${color}`]"
    :body-style="{ padding: '20px' }"
  >
    <div v-if="loading" class="stat-card__skeleton">
      <a-skeleton active :paragraph="{ rows: 1 }" />
    </div>
    <div v-else class="stat-card__content">
      <div class="stat-card__header">
        <div class="stat-card__icon">
          <slot name="icon">
            <SvgIcon :icon="svgIconName" />
          </slot>
        </div>
        <div v-if="trend" class="stat-card__trend" :class="`stat-card__trend--${trendType}`">
          <ArrowUpOutlined v-if="trendType === 'up'" />
          <ArrowDownOutlined v-else-if="trendType === 'down'" />
          <MinusOutlined v-else />
          <span>{{ trend }}</span>
        </div>
      </div>
      <div class="stat-card__value">{{ displayValue }}</div>
      <div class="stat-card__title">{{ title }}</div>
    </div>
  </a-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons-vue'
import SvgIcon from '@/components/SvgIcon/index.vue'

// Ant Design 图标名 → SvgIcon 图标名映射
const iconNameMap: Record<string, string> = {
  BarChartOutlined: 'icon-outlined-bar-chart',
  ClockCircleOutlined: 'icon-outlined-clock-circle',
  BookOutlined: 'icon-outlined-book',
  TrophyOutlined: 'icon-outlined-trophy',
  UserOutlined: 'icon-outlined-user',
  LineChartOutlined: 'icon-outlined-line-chart',
  CalendarOutlined: 'icon-outlined-calendar',
  FireOutlined: 'icon-outlined-fire',
  AimOutlined: 'icon-outlined-aim',
  ReloadOutlined: 'icon-outlined-reload',
}

interface Props {
  title: string
  value: string | number
  loading?: boolean
  color?: 'blue' | 'green' | 'orange' | 'red' | 'purple' | 'cyan' | 'geekblue'
  icon?: string
  trend?: string
  trendType?: 'up' | 'down' | 'neutral'
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  color: 'blue',
  trend: '',
  trendType: 'neutral',
})

const svgIconName = computed(() => {
  return iconNameMap[props.icon ?? ''] ?? 'icon-outlined-bar-chart'
})

const displayValue = computed(() => {
  if (typeof props.value === 'number') {
    return props.value.toLocaleString()
  }
  return props.value
})
</script>

<style scoped>
@reference "#main.css";

.stat-card {
  @apply transition-all duration-300 hover:shadow-lg;
}

.stat-card--loading {
  @apply opacity-60;
}

.stat-card__content {
  @apply flex flex-col gap-3;
}

.stat-card__header {
  @apply flex items-center justify-between;
}

.stat-card__icon {
  @apply flex items-center justify-center w-10 h-10 rounded-lg text-xl;
}

.stat-card--blue .stat-card__icon {
  @apply bg-blue-50 text-blue-500 dark:bg-blue-900/30 dark:text-blue-400;
}

.stat-card--green .stat-card__icon {
  @apply bg-green-50 text-green-500 dark:bg-green-900/30 dark:text-green-400;
}

.stat-card--orange .stat-card__icon {
  @apply bg-orange-50 text-orange-500 dark:bg-orange-900/30 dark:text-orange-400;
}

.stat-card--red .stat-card__icon {
  @apply bg-red-50 text-red-500 dark:bg-red-900/30 dark:text-red-400;
}

.stat-card--purple .stat-card__icon {
  @apply bg-purple-50 text-purple-500 dark:bg-purple-900/30 dark:text-purple-400;
}

.stat-card--cyan .stat-card__icon {
  @apply bg-cyan-50 text-cyan-500 dark:bg-cyan-900/30 dark:text-cyan-400;
}

.stat-card--geekblue .stat-card__icon {
  @apply bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400;
}

.stat-card__trend {
  @apply flex items-center gap-1 text-xs font-medium;
}

.stat-card__trend--up {
  @apply text-green-500;
}

.stat-card__trend--down {
  @apply text-red-500;
}

.stat-card__trend--neutral {
  @apply text-gray-400;
}

.stat-card__value {
  @apply text-2xl font-bold text-gray-800 dark:text-gray-100;
}

.stat-card__title {
  @apply text-sm text-gray-500 dark:text-gray-400;
}

.stat-card__skeleton {
  @apply py-2;
}
</style>
