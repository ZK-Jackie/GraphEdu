<template>
  <a-switch
    v-bind="$attrs"
    :checked="isChecked"
    :loading="loading"
    :checked-children="checkedLabel"
    :un-checked-children="uncheckedLabel"
    @change="handleChange"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { getDictDataByType } from '@/api/system/dict.ts'
import type { DictItem } from '@/types/stores/dict.ts'
import useDictStore from '@/stores/modules/dict.ts'
import type { DictType } from '@/types/api/system/dict.ts'

interface Props {
  /** 字典类型（如：sys_normal_disable）需要是二元值的字典 */
  dictType: string
  /** 当前值（v-model） */
  modelValue?: DictType | number | undefined
  /** 选中状态的值（默认：'1' 或 1） */
  checkedValue?: string | number
  /** 未选中状态的值（默认：'0' 或 0） */
  uncheckedValue?: string | number
  /** 选中状态的显示文本（如：'启用'、'是'），不传则使用字典标签 */
  checkedLabel?: string
  /** 未选中状态的显示文本（如：'禁用'、'否'），不传则使用字典标签 */
  uncheckedLabel?: string
}

interface Emits {
  (e: 'update:modelValue', value: string | number): void
  (e: 'change', value: string | number, option: DictItem): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: undefined,
  checkedValue: '1',
  uncheckedValue: '0',
  checkedLabel: '',
  uncheckedLabel: '',
})

const emit = defineEmits<Emits>()

const dictStore = useDictStore()
const loading = ref(false)
const dictOptions = ref<DictItem[]>([])

// 是否选中
const isChecked = computed(() => {
  return props.modelValue === props.checkedValue
})

// 选中状态的标签
const computedCheckedLabel = computed(() => {
  if (props.checkedLabel) return props.checkedLabel
  const option = dictOptions.value.find((item) => item.value === props.checkedValue)
  return option?.label ?? ''
})

// 未选中状态的标签
const computedUncheckedLabel = computed(() => {
  if (props.uncheckedLabel) return props.uncheckedLabel
  const option = dictOptions.value.find((item) => item.value === props.uncheckedValue)
  return option?.label ?? ''
})

/**
 * 加载字典数据
 */
async function loadDictData() {
  if (!props.dictType) return

  loading.value = true
  try {
    // 先从本地缓存获取
    const cached = dictStore.getDict(props.dictType)
    if (cached && cached.length > 0) {
      dictOptions.value = cached
      loading.value = false
      return
    }

    // 缓存未命中，从服务器获取
    const res = await getDictDataByType(props.dictType)
    if (res.code === 200 && res.data) {
      dictOptions.value = res.data.map((p) => ({
        label: p.dictLabel,
        value: p.dictValue,
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
    message.error(`加载字典数据失败: ${props.dictType}`)
    dictOptions.value = []
  } finally {
    loading.value = false
  }
}

/**
 * 处理开关变化
 */
function handleChange(checked: boolean | string | number, _e: Event) {
  const newValue = checked ? props.checkedValue : props.uncheckedValue
  const option = dictOptions.value.find((item) => item.value === newValue)
  emit('update:modelValue', newValue)
  emit('change', newValue, option as DictItem)
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
/* 继承父组件样式 */
</style>
