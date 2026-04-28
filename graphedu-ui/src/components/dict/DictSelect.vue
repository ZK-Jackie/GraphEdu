<template>
  <a-select
    v-bind="$attrs"
    v-model:value="innerValue"
    :placeholder="placeholder"
    :allow-clear="allowClear"
    :loading="loading"
    @change="handleChange"
  >
    <a-select-option v-for="item in dictOptions" :key="item.value" :value="item.value" :disabled="item.disabled">
      <span v-if="!renderStyle" class="dict-select-text">
        <SvgIcon v-if="item.icon" :icon="item.icon" class="dict-select-icon" />
        {{ item.label }}
      </span>
      <a-tag v-else :color="item.tagType" :style="item.style" :bordered="item.bordered === 'Y'">
        <SvgIcon v-if="item.icon" :icon="item.icon" class="dict-select-icon" />
        {{ item.label }}
      </a-tag>
    </a-select-option>
  </a-select>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import type { DefaultOptionType } from 'ant-design-vue/es/select'
import { getDictDataByType } from '@/api/system/dict.ts'
import type { DictItem } from '@/types/stores/dict.ts'
import useDictStore from '@/stores/modules/dict.ts'
import SvgIcon from '@/components/SvgIcon/index.vue'
import type { DictType } from '@/types/api/system/dict.ts'

interface Props {
  /** 字典类型（如：sys_user_sex, sys_normal_disable） */
  dictType: string
  /** 当前值（v-model） */
  modelValue?: DictType | number | undefined
  /** 占位符 */
  placeholder?: string
  /** 是否允许清空 */
  allowClear?: boolean
  /** 是否渲染样式 */
  renderStyle?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: string | number | undefined): void
  (e: 'change', value: string | number | undefined, option: DictItem): void
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '请选择',
  allowClear: true,
  modelValue: undefined,
  renderStyle: false,
})

const emit = defineEmits<Emits>()

const dictStore = useDictStore()
const loading = ref(false)
const dictOptions = ref<DictItem[]>([])

// 内部值
const innerValue = computed({
  get: () => props.modelValue,
  set: (val) => {
    emit('update:modelValue', val)
  },
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
 * 处理选择变化
 */
function handleChange(value: any, _option: DefaultOptionType | DefaultOptionType[]) {
  const option = dictOptions.value.find((item) => item.value === value)
  emit('change', value, option as DictItem)
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
.dict-select-text {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.dict-select-icon {
  margin-right: 4px;
}
</style>
