<template>
  <div class="dict-label-container">
    <template v-if="Array.isArray(value) || (typeof value === 'string' && value.includes(','))">
      <!-- 多值模式 -->
      <template v-for="item in valueArray" :key="item">
        <span
          v-if="!getDictItem(item)?.tagType || getDictItem(item)?.tagType === 'default'"
          class="dict-label-text"
          :style="getDictItem(item)?.style"
        >
          <SvgIcon v-if="getDictItem(item)?.icon" :icon="getDictItem(item)!.icon!" class="dict-label-icon" />
          {{ getDictItem(item)?.label || item }}
        </span>
        <a-tag
          v-else
          :color="getDictItem(item)?.tagType || 'default'"
          :style="getDictItem(item)?.style"
          :bordered="getDictItem(item)?.bordered === 'Y'"
        >
          <SvgIcon v-if="getDictItem(item)?.icon" :icon="getDictItem(item)!.icon!" class="dict-label-icon" />
          {{ getDictItem(item)?.label || item }}
        </a-tag>
      </template>
    </template>
    <template v-else>
      <!-- 单值模式 -->
      <span
        v-if="!currentDictItem?.tagType || currentDictItem?.tagType === 'default'"
        class="dict-label-text"
        :style="currentDictItem?.style"
      >
        <SvgIcon v-if="currentDictItem?.icon" :icon="currentDictItem!.icon" class="dict-label-icon" />
        {{ currentDictItem?.label || value }}
      </span>
      <a-tag
        v-else
        :color="currentDictItem?.tagType || 'default'"
        :style="currentDictItem?.style"
        :bordered="currentDictItem?.bordered === 'Y'"
      >
        <SvgIcon v-if="currentDictItem?.icon" :icon="currentDictItem!.icon" class="dict-label-icon" />
        {{ currentDictItem?.label || value }}
      </a-tag>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { getDictDataByType } from '@/api/system/dict.ts'
import type { DictItem } from '@/types/stores/dict.ts'
import useDictStore from '@/stores/modules/dict.ts'
import SvgIcon from '@/components/SvgIcon/index.vue'

interface Props {
  /** 字典类型（如：sys_user_sex, sys_normal_disable） */
  dictType: string
  /** 字典值（单个或多个，多个用逗号分隔） */
  value?: string | number | (string | number)[]
  /** 分隔符（当 value 为字符串时） */
  separator?: string
  /** 当未找到匹配的数据时，是否显示原值 */
  showValue?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  separator: ',',
  showValue: true,
  value: '',
})

const dictStore = useDictStore()
const dictOptions = ref<DictItem[]>([])

/**
 * 获取字典项
 */
function getDictItem(val: string | number): DictItem | undefined {
  return dictOptions.value.find((item) => item.value === String(val))
}

/**
 * 解析后的值数组
 */
const valueArray = computed(() => {
  if (props.value === null || props.value === undefined || props.value === '') return []
  if (Array.isArray(props.value)) return props.value.map((item) => String(item))
  return String(props.value).split(props.separator)
})

/**
 * 当前字典项（单值模式）
 */
const currentDictItem = computed(() => {
  if (props.value === null || props.value === undefined || props.value === '') return undefined
  const valueStr = String(props.value)
  return dictOptions.value.find((item) => item.value === valueStr)
})

/**
 * 加载字典数据
 */
async function loadDictData() {
  if (!props.dictType) return

  try {
    // 先从本地缓存获取
    const cached = dictStore.getDict(props.dictType)
    if (cached && cached.length > 0) {
      dictOptions.value = cached
      return
    }

    // 缓存未命中，从服务器获取
    const res = await getDictDataByType(props.dictType)
    if (res.code === 200 && res.data) {
      dictOptions.value = res.data.map((p) => ({
        label: p.dictLabel,
        value: String(p.dictValue),
        tagType: p.color ?? 'default',
        style: p.style ?? {},
        icon: p.icon ?? '',
        bordered: p.bordered ?? 'N',
        disabled: false,
      }))
      // 存入缓存
      dictStore.setDict(props.dictType, dictOptions.value)
    }
  } catch (_e) {
    // 静默失败，显示原值
    dictOptions.value = []
  }
}

// 监听字典类型变化
watch(
  () => props.dictType,
  () => {
    loadDictData()
  },
  { immediate: true }
)
</script>

<style scoped>
.dict-label-container {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.dict-label-text {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.dict-label-icon {
  margin-right: 4px;
}
</style>
