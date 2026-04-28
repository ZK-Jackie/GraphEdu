<template>
  <div class="dict-tag-container">
    <template v-for="item in options" :key="item.value">
      <template v-if="values.includes(item.value)">
        <!-- 无颜色或默认颜色 - 显示为普通文本 -->
        <span v-if="!item.tagType" class="dict-tag-text" :style="item.style">
          <SvgIcon v-if="item.icon" :icon="item.icon" class="dict-tag-icon" />
          {{ item.label }}
        </span>
        <!-- 有颜色 - 显示为 Tag -->
        <a-tag v-else :color="item.tagType" :style="item.style" :bordered="item.bordered === 'Y'">
          <SvgIcon v-if="item.icon" :icon="item.icon" class="dict-tag-icon" />
          {{ item.label }}
        </a-tag>
      </template>
    </template>
    <!-- 未匹配的值 -->
    <template v-if="unmatch && showValue">
      {{ unmatchArray.join(' ') }}
    </template>
  </div>
</template>

<script setup lang="ts">
import type { DictItem } from '@/types/stores/dict.ts'
import SvgIcon from '@/components/SvgIcon/index.vue'

interface Props {
  /** 字典选项数据 */
  options?: DictItem[]
  /** 当前值（单个或数组） */
  value?: string | number | (string | number)[]
  /** 当未找到匹配的数据时，是否显示原值 */
  showValue?: boolean
  /** 分隔符（当 value 为字符串时） */
  separator?: string
}

const props = withDefaults(defineProps<Props>(), {
  options: () => [],
  showValue: true,
  separator: ',',
  value: '',
})

/** 解析后的值数组 */
const values = computed(() => {
  if (props.value === null || props.value === undefined || props.value === '') return []
  if (Array.isArray(props.value)) return props.value.map((item) => String(item))
  return String(props.value).split(props.separator)
})

/** 未匹配的值数组 */
const unmatchArray = computed(() => {
  if (
    props.value === null ||
    props.value === undefined ||
    props.value === '' ||
    !Array.isArray(props.options) ||
    props.options.length === 0
  )
    return []

  return values.value.filter((item) => !props.options.some((v) => v.value === item))
})

/** 是否有未匹配的值 */
const unmatch = computed(() => unmatchArray.value.length > 0)
</script>

<style scoped>
.dict-tag-container {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.dict-tag-text {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.dict-tag-icon {
  margin-right: 4px;
}
</style>
