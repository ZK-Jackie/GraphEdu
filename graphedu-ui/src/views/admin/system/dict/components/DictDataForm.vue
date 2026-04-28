<template>
  <a-modal
    :open="visible"
    :title="title"
    :confirm-loading="loading"
    width="600px"
    @ok="handleSubmit"
    @cancel="handleCancel"
  >
    <a-form ref="formRef" :model="formData" :rules="rules as any" :label-col="{ span: 6 }">
      <a-form-item :label="t('system.dict.dictTypeValue')">
        <a-input v-model:value="formData.dictType" disabled />
      </a-form-item>
      <a-form-item :label="t('system.dict.dictLabel')" name="dictLabel">
        <a-input v-model:value="formData.dictLabel" :placeholder="t('system.dict.dictLabelPlaceholder')" />
      </a-form-item>
      <a-form-item :label="t('system.dict.dictValue')" name="dictValue">
        <a-input v-model:value="formData.dictValue" :placeholder="t('system.dict.dictValuePlaceholder')" />
      </a-form-item>
      <a-form-item :label="t('common.sortDisplay')" name="dictSort">
        <a-input-number v-model:value="formData.dictSort" :min="0" style="width: 100%" />
      </a-form-item>
      <a-form-item :label="t('system.dict.colorTheme')" name="color">
        <a-select v-model:value="formData.color" :placeholder="t('system.dict.colorThemePlaceholder')">
          <a-select-option value="default">{{ t('system.dict.colorDefault') }} (default)</a-select-option>
          <a-select-option value="processing">{{ t('system.dict.colorProcessing') }} (processing)</a-select-option>
          <a-select-option value="success">{{ t('system.dict.colorSuccess') }} (success)</a-select-option>
          <a-select-option value="error">{{ t('system.dict.colorError') }} (error)</a-select-option>
          <a-select-option value="warning">{{ t('system.dict.colorWarning') }} (warning)</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item :label="t('system.dict.iconName')" name="icon">
        <a-input v-model:value="formData.icon" :placeholder="t('system.dict.iconNamePlaceholder')" />
      </a-form-item>
      <a-form-item :label="t('system.dict.hasBorder')" name="bordered">
        <DictRadio v-model:model-value="formData.bordered" dict-type="sys_data_option" />
      </a-form-item>
      <a-form-item :label="t('system.dict.isDefault')" name="isDefault">
        <DictRadio v-model:model-value="formData.isDefault" dict-type="sys_data_option" />
      </a-form-item>
      <a-form-item :label="t('common.status')" name="status">
        <DictRadio v-model:model-value="formData.status" dict-type="sys_data_status" />
      </a-form-item>
      <a-form-item :label="t('common.remark')" name="remark">
        <a-textarea v-model:value="formData.remark" :placeholder="t('common.remarkPlaceholder')" :rows="3" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { addDictData, updateDictData, getDictDataDetail } from '@/api/system/dict.ts'
import type { DictDataCreateDTO, DictDataUpdateDTO } from '@/types/api/system/dict.ts'
import DictRadio from '../../../../../components/dict/DictRadio.vue'

const { t } = useI18n()

interface Props {
  visible: boolean
  dictCode?: number
  dictType: string
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref()
const loading = ref(false)

const title = computed(() => (props.dictCode ? t('system.dict.editDictData') : t('system.dict.addDictData')))

const formData = reactive<DictDataCreateDTO & { dictCode?: number }>({
  dictLabel: '',
  dictValue: '',
  dictType: '', // 初始为空，通过 watch immediate 立即同步 props.dictType
  dictSort: 0,
  style: {},
  color: 'default',
  icon: '',
  bordered: 'N',
  isDefault: 'N',
  status: '0',
  remark: '',
})

const rules = {
  dictLabel: [{ required: true, message: t('system.dict.dictLabelRequired'), trigger: 'blur' }],
  dictValue: [{ required: true, message: t('system.dict.dictValueRequired'), trigger: 'blur' }],
  dictSort: [{ required: true, message: t('system.dict.dictSortRequired'), trigger: 'blur' }],
}

// 重置表单
const resetForm = () => {
  formData.dictCode = undefined
  formData.dictLabel = ''
  formData.dictValue = ''
  formData.dictType = props.dictType
  formData.dictSort = 0
  formData.style = {}
  formData.color = 'default'
  formData.icon = ''
  formData.bordered = 'N'
  formData.isDefault = 'N'
  formData.status = '0'
  formData.remark = ''
  formRef.value?.resetFields()
}

// 监听 visible 变化
watch(
  () => props.visible,
  async (val) => {
    if (val && props.dictCode) {
      // 编辑模式，获取详情
      loading.value = true
      try {
        const res = await getDictDataDetail(props.dictCode)
        if (res.code === 200 && res.data) {
          Object.assign(formData, res.data)
        }
      } catch (_e) {
        message.error(t('system.dict.getDictDataDetailFailed'))
      } finally {
        loading.value = false
      }
    } else if (val) {
      // 新增模式
      resetForm()
    }
  }
)

// 监听 dictType 变化
watch(
  () => props.dictType,
  (val) => {
    formData.dictType = val
  },
  { immediate: true } // 初始化时立即执行一次
)

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    loading.value = true

    let res
    if (props.dictCode) {
      // 修改
      const updateData: DictDataUpdateDTO = {
        dictCode: props.dictCode,
        dictLabel: formData.dictLabel,
        dictValue: formData.dictValue,
        dictType: formData.dictType,
        dictSort: formData.dictSort,
        style: formData.style,
        color: formData.color,
        icon: formData.icon,
        bordered: formData.bordered as 'Y' | 'N',
        isDefault: formData.isDefault as 'Y' | 'N',
        status: formData.status as '0' | '1',
        remark: formData.remark,
      }
      res = await updateDictData(updateData)
    } else {
      // 新增
      const createData: DictDataCreateDTO = {
        dictLabel: formData.dictLabel,
        dictValue: formData.dictValue,
        dictType: formData.dictType,
        dictSort: formData.dictSort,
        style: formData.style,
        color: formData.color,
        icon: formData.icon,
        bordered: formData.bordered as 'Y' | 'N',
        isDefault: formData.isDefault as 'Y' | 'N',
        status: formData.status as '0' | '1',
        remark: formData.remark,
      }
      res = await addDictData(createData)
    }

    if (res.code === 200) {
      message.success(props.dictCode ? t('common.updateSuccess') : t('common.addSuccess'))
      emit('success')
      handleCancel()
    }
  } catch (_e) {
    // 验证失败或接口错误
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  emit('update:visible', false)
  resetForm()
}
</script>
