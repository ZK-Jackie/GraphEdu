<template>
  <a-modal
    :open="visible"
    :title="title"
    :confirm-loading="loading"
    width="500px"
    @ok="handleSubmit"
    @cancel="handleCancel"
  >
    <a-form ref="formRef" :model="formData" :rules="rules as any" :label-col="{ span: 6 }">
      <a-form-item :label="t('system.dict.dictType')" name="dictName">
        <a-input v-model:value="formData.dictName" :placeholder="t('system.dict.dictNamePlaceholder')" />
      </a-form-item>
      <a-form-item :label="t('system.dict.dictTypeValue')" name="dictType">
        <a-input v-model:value="formData.dictType" :placeholder="t('system.dict.dictTypeValuePlaceholder')" />
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
import { addDictType, updateDictType, getDictTypeDetail } from '@/api/system/dict.ts'
import type { DictTypeCreateDTO, DictTypeUpdateDTO } from '@/types/api/system/dict.ts'
import DictRadio from '../../../../../components/dict/DictRadio.vue'

const { t } = useI18n()

interface Props {
  visible: boolean
  dictId?: number
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref()
const loading = ref(false)

const title = computed(() => (props.dictId ? t('system.dict.editDictType') : t('system.dict.addDictType')))

const formData = reactive<DictTypeCreateDTO & { dictId?: number }>({
  dictName: '',
  dictType: '',
  status: '0',
  remark: '',
})

const rules = {
  dictName: [{ required: true, message: t('system.dict.dictNameRequired'), trigger: 'blur' }],
  dictType: [{ required: true, message: t('system.dict.dictTypeValueRequired'), trigger: 'blur' }],
}

// 重置表单
const resetForm = () => {
  formData.dictId = undefined
  formData.dictName = ''
  formData.dictType = ''
  formData.status = '0'
  formData.remark = ''
  formRef.value?.resetFields()
}

// 监听 visible 变化
watch(
  () => props.visible,
  async (val) => {
    if (val && props.dictId) {
      // 编辑模式，获取详情
      loading.value = true
      try {
        const res = await getDictTypeDetail(props.dictId)
        if (res.code === 200 && res.data) {
          Object.assign(formData, res.data)
        }
      } catch (_e) {
        message.error(t('system.dict.getDictTypeDetailFailed'))
      } finally {
        loading.value = false
      }
    } else if (val) {
      // 新增模式
      resetForm()
    }
  }
)

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    loading.value = true

    let res
    if (props.dictId) {
      // 修改
      const updateData: DictTypeUpdateDTO = {
        dictId: props.dictId,
        dictName: formData.dictName,
        dictType: formData.dictType,
        status: formData.status as '0' | '1',
        remark: formData.remark,
      }
      res = await updateDictType(updateData)
    } else {
      // 新增
      const createData: DictTypeCreateDTO = {
        dictName: formData.dictName,
        dictType: formData.dictType,
        status: formData.status as '0' | '1',
        remark: formData.remark,
      }
      res = await addDictType(createData)
    }

    if (res.code === 200) {
      message.success(props.dictId ? t('common.updateSuccess') : t('common.addSuccess'))
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
