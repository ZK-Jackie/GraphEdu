<template>
  <a-modal
    :open="visible"
    :title="title"
    :confirm-loading="loading"
    :width="800"
    @cancel="handleCancel"
    @ok="handleSubmit"
  >
    <a-spin :spinning="detailLoading" :tip="t('common.loading')">
      <a-form ref="formRef" :model="form" :rules="rules as any" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-row>
          <a-col :span="24">
            <a-form-item :label="t('system.function.parentFunction')" name="parentId">
              <a-tree-select
                v-model:value="form.parentId"
                tree-node-filter-prop="functionName"
                :tree-data="functionTreeData"
                :field-names="{ value: 'functionId', label: 'functionName', children: 'children' }"
                :placeholder="t('system.function.parentFunctionPlaceholder')"
                :dropdown-style="{ maxHeight: '400px', overflow: 'auto' }"
                tree-default-expand-all
                :tree-default-value="0"
              />
            </a-form-item>
          </a-col>

          <a-col :span="24">
            <a-form-item :label="t('system.function.functionType')" name="functionType">
              <DictRadio v-model:model-value="form.functionType" dict-type="sys_function_type" />
            </a-form-item>
          </a-col>

          <!-- 场景选择（所有类型都需要） -->
          <a-col :span="24">
            <a-form-item :label="t('system.function.scene')" name="scene">
              <DictSelect
                v-model:model-value="form.scene"
                dict-type="sys_function_scene"
                :placeholder="t('system.function.scenePlaceholder')"
                allow-clear
              />
            </a-form-item>
          </a-col>

          <a-col v-show="form.functionType === 'DIR' || form.functionType === 'MENU'" :span="12">
            <a-form-item :label="t('system.function.icon')" name="icon">
              <a-input-group compact>
                <a-input
                  v-model:value="form.icon"
                  :placeholder="t('system.function.iconPlaceholder')"
                  readonly
                  style="width: calc(100% - 32px)"
                >
                  <template #prefix>
                    <SvgIcon v-if="form.icon" :icon="form.icon" :size="16" />
                  </template>
                </a-input>
                <a-button @click="iconSelectRef?.open()">
                  <template #icon><SearchOutlined /></template>
                </a-button>
              </a-input-group>
            </a-form-item>
          </a-col>

          <a-col :span="12">
            <a-form-item :label="t('common.sortDisplay')" name="sortOrder">
              <a-input-number v-model:value="form.sortOrder" :min="0" style="width: 100%" />
            </a-form-item>
          </a-col>

          <a-col :span="12">
            <a-form-item :label="t('system.function.functionName')" name="functionName">
              <a-input v-model:value="form.functionName" :placeholder="t('system.function.functionNamePlaceholder')" />
            </a-form-item>
          </a-col>

          <a-col v-show="form.functionType !== 'GROUP' && form.functionType !== 'DIVIDER'" :span="12">
            <a-form-item :label="t('system.function.permission')" name="functionKey">
              <a-input v-model:value="form.functionKey" :placeholder="t('system.function.permissionPlaceholder')" />
            </a-form-item>
          </a-col>

          <a-col v-show="form.functionType === 'DIR' || form.functionType === 'MENU'" :span="12">
            <a-form-item :label="t('system.function.routePath')" name="routePath">
              <a-input v-model:value="form.routePath" :placeholder="t('system.function.routePathPlaceholder')" />
            </a-form-item>
          </a-col>

          <a-col v-show="form.functionType === 'MENU' || form.functionType === 'DIR'" :span="12">
            <a-form-item :label="t('system.function.component')" name="component">
              <a-input v-model:value="form.component" :placeholder="t('system.function.componentPlaceholder')" />
              <div class="form-item-tip">{{ t('system.function.componentTip') }}</div>
            </a-form-item>
          </a-col>

          <!-- 布局组件（DIR 和 MENU 类型显示） -->
          <a-col v-show="form.functionType === 'MENU' || form.functionType === 'DIR'" :span="12">
            <a-form-item :label="t('system.function.layoutComponent')" name="layoutComponent">
              <a-input
                v-model:value="form.layoutComponent"
                :placeholder="t('system.function.layoutComponentPlaceholder')"
              />
              <div class="form-item-tip">{{ t('system.function.layoutComponentTip') }}</div>
            </a-form-item>
          </a-col>

          <!-- 菜单样式（DIR/MENU 类型显示） -->
          <a-col v-show="form.functionType === 'DIR' || form.functionType === 'MENU'" :span="12">
            <a-form-item :label="t('system.function.style')" name="style">
              <a-input v-model:value="form.style" :placeholder="t('system.function.stylePlaceholder')" />
              <div class="form-item-tip">{{ t('system.function.styleTip') }}</div>
            </a-form-item>
          </a-col>

          <!-- 选项样式（DIR/MENU 类型显示） -->
          <a-col v-show="form.functionType === 'DIR' || form.functionType === 'MENU'" :span="12">
            <a-form-item :label="t('system.function.optionStyle')" name="optionStyle">
              <a-input v-model:value="form.optionStyle" :placeholder="t('system.function.optionStylePlaceholder')" />
              <div class="form-item-tip">{{ t('system.function.optionStyleTip') }}</div>
            </a-form-item>
          </a-col>

          <a-col v-show="form.functionType === 'MENU'" :span="12">
            <a-form-item :label="t('system.function.routeQuery')" name="routeQuery">
              <a-input v-model:value="form.routeQuery" :placeholder="t('system.function.routeQueryPlaceholder')" />
              <div class="form-item-tip">{{ t('system.function.routeQueryTip') }}</div>
            </a-form-item>
          </a-col>

          <a-col v-show="form.functionType === 'MENU'" :span="12">
            <a-form-item :label="t('system.function.routeExternal')" name="routeExternal">
              <DictRadio v-model:model-value="form.routeExternal" dict-type="sys_data_option" />
            </a-form-item>
          </a-col>

          <a-col v-show="form.functionType === 'MENU'" :span="12">
            <a-form-item :label="t('system.function.routeCache')" name="routeCache">
              <DictRadio v-model:model-value="form.routeCache" dict-type="sys_data_option" />
            </a-form-item>
          </a-col>

          <a-col v-show="form.functionType !== 'BUTTON' && form.functionType !== 'INTERFACE'" :span="12">
            <a-form-item :label="t('system.function.visible')" name="visible">
              <DictRadio v-model:model-value="form.visible" dict-type="sys_data_option" />
            </a-form-item>
          </a-col>

          <a-col :span="12">
            <a-form-item :label="t('common.status')" name="status">
              <DictRadio v-model:model-value="form.status" dict-type="sys_data_status" />
            </a-form-item>
          </a-col>

          <a-col v-show="form.functionType !== 'DIVIDER'" :span="24">
            <a-form-item :label="t('common.remark')" name="remark">
              <a-textarea v-model:value="form.remark" :placeholder="t('common.remarkPlaceholder')" :rows="3" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-spin>
  </a-modal>

  <!-- Icon 选择器 -->
  <IconSelect ref="iconSelectRef" v-model="form.icon" />
</template>

<script setup lang="ts">
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import type { FormInstance } from 'ant-design-vue'
import { SearchOutlined } from '@ant-design/icons-vue'
import { addFunction, updateFunction, getFunctionDetail, getFunctionTreeSelect } from '@/api/system/function.ts'
import type {
  FunctionCreateDTO,
  FunctionUpdateDTO,
  FunctionTreeVO,
  FunctionTreeBriefVO,
  FunctionType,
} from '@/types/api/system/function.ts'
import IconSelect from '@/components/IconSelect/index.vue'
import DictRadio from '../../../../../components/dict/DictRadio.vue'
import DictSelect from '@/components/dict/DictSelect.vue'

const { t } = useI18n()

interface Props {
  visible: boolean
  functionId?: number
  parentId?: number
  parentScene?: string
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const loading = ref(false)
const detailLoading = ref(false)
const functionTreeData = ref<FunctionTreeBriefVO[]>([])
const iconSelectRef = ref<InstanceType<typeof IconSelect>>()

// 是否编辑模式
const isEdit = computed(() => !!props.functionId)

// 弹窗标题
const title = computed(() => (isEdit.value ? t('system.function.editFunction') : t('system.function.addFunction')))

// 表单数据
interface FunctionFormState {
  parentId: number | undefined
  functionName: string
  functionKey: string
  functionType: FunctionType
  scene: string
  routePath: string
  routeCache: string
  routeExternal: string
  routeQuery: string
  component: string
  layoutComponent: string
  icon: string
  sortOrder: number
  visible: string
  status: string
  style: string
  optionStyle: string
  remark: string
}

const form = reactive<FunctionFormState>({
  parentId: 0,
  functionName: '根节点',
  functionKey: '',
  functionType: 'DIR',
  scene: 'admin',
  routePath: '',
  routeCache: 'N',
  routeExternal: 'N',
  routeQuery: '',
  component: '',
  layoutComponent: '',
  icon: '',
  sortOrder: 0,
  visible: 'Y',
  status: '0',
  style: '',
  optionStyle: '',
  remark: '',
})

// 表单验证规则
const rules = {
  functionName: [{ required: true, message: t('system.function.functionNameRequired'), trigger: 'blur' }],
  functionKey: [
    {
      validator: (_rule: any, value: string) => {
        const type = form.functionType
        if (type !== 'GROUP' && type !== 'DIVIDER' && !value?.trim()) {
          return Promise.reject(t('system.function.permissionRequired') || '权限标识不能为空')
        }
        return Promise.resolve()
      },
      trigger: 'blur',
    },
  ],
  sortOrder: [{ required: true, message: t('common.sortRequired'), trigger: 'blur' }],
  routePath: [
    {
      validator: (_rule: any, value: string) => {
        if ((form.functionType === 'DIR' || form.functionType === 'MENU') && !value?.trim()) {
          return Promise.reject(t('system.function.routePathRequired'))
        }
        return Promise.resolve()
      },
      trigger: 'blur',
    },
  ],
  routeQuery: [
    {
      validator: (_rule: any, value: string) => {
        if (value && !validateJson(value)) {
          return Promise.reject(t('system.function.routeQueryFormatError'))
        }
        return Promise.resolve()
      },
      trigger: 'blur',
    },
  ],
  style: [
    {
      validator: (_rule: any, value: string) => {
        if (value && !validateJson(value)) {
          return Promise.reject(t('system.function.styleFormatError'))
        }
        return Promise.resolve()
      },
      trigger: 'blur',
    },
  ],
  optionStyle: [
    {
      validator: (_rule: any, value: string) => {
        if (value && !validateJson(value)) {
          return Promise.reject(t('system.function.optionStyleFormatError'))
        }
        return Promise.resolve()
      },
      trigger: 'blur',
    },
  ],
}

// JSON 验证器
const validateJson = (value: string): boolean => {
  if (!value || !value.trim()) return true
  try {
    JSON.parse(value)
    return true
  } catch {
    return false
  }
}

// 根据功能类型过滤字段
const filterFieldsByType = (functionType: FunctionType, rawData: any) => {
  const baseFields = ['parentId', 'sortOrder', 'visible', 'status', 'scene', 'remark', 'functionType']
  const routeFields = ['routePath', 'routeCache', 'routeQuery', 'routeExternal', 'icon']
  const componentFields = ['component', 'layoutComponent']
  const styleFields = ['style', 'optionStyle']

  let allowedFields: string[] = []

  switch (functionType) {
    case 'BUTTON':
    case 'INTERFACE':
      allowedFields = [...baseFields, 'functionName', 'functionKey']
      break
    case 'DIR':
      allowedFields = [
        ...baseFields,
        'functionName',
        'functionKey',
        'routePath',
        'icon',
        ...componentFields,
        ...styleFields,
      ]
      break
    case 'MENU':
      allowedFields = [...baseFields, 'functionName', 'functionKey', ...routeFields, ...componentFields, ...styleFields]
      break
    case 'GROUP':
      allowedFields = [...baseFields, 'functionName']
      break
    case 'DIVIDER':
      allowedFields = ['parentId', 'sortOrder', 'visible', 'status', 'scene', 'functionType', 'functionName']
      break
    default:
      return rawData
  }

  // 构建过滤后的对象
  const filtered: any = {}
  allowedFields.forEach((field) => {
    if (rawData[field] !== undefined && rawData[field] !== '') {
      filtered[field] = rawData[field]
    }
  })

  return filtered
}

// 获取功能树
const getFunctionTree = async () => {
  try {
    const res = await getFunctionTreeSelect()
    if (res.code === 200) {
      // 添加根节点（FunctionTreeBriefVO 只包含必要字段）
      functionTreeData.value = [
        {
          functionId: 0,
          parentId: -1,
          functionName: t('system.function.rootCategory'),
          functionType: 'DIR' as FunctionType,
          children: res.data || [],
        },
      ]
    }
  } catch (_e) {
    message.error(t('system.function.getFunctionTreeFailed'))
  }
}

// 获取功能详情
const getFunctionInfo = async () => {
  if (!props.functionId) return

  detailLoading.value = true
  try {
    const res = await getFunctionDetail(props.functionId)
    if (res.code === 200) {
      const detail = res.data
      Object.assign(form, {
        parentId: detail.parentId,
        functionName: detail.functionName,
        functionKey: detail.functionKey,
        functionType: detail.functionType,
        scene: detail.scene,
        routePath: detail.routePath,
        routeCache: detail.routeCache,
        routeExternal: detail.routeExternal,
        routeQuery: detail.routeQuery ? JSON.stringify(detail.routeQuery) : '',
        component: detail.component,
        layoutComponent: detail.layoutComponent || '',
        icon: detail.icon,
        sortOrder: detail.sortOrder,
        visible: detail.visible,
        status: detail.status,
        style: detail.style ? JSON.stringify(detail.style) : '',
        optionStyle: detail.optionStyle ? JSON.stringify(detail.optionStyle) : '',
        remark: detail.remark,
      })
    }
  } catch (_e) {
    message.error(t('system.function.getFunctionInfoFailed'))
  } finally {
    detailLoading.value = false
  }
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(form, {
    parentId: props.parentId ?? 0,
    functionName: '',
    functionKey: '',
    functionType: 'DIR',
    scene: props.parentScene ?? 'admin',
    routePath: '',
    routeCache: 'N',
    routeExternal: 'N',
    routeQuery: '',
    component: '',
    layoutComponent: '',
    icon: '',
    sortOrder: 0,
    visible: 'Y',
    status: '0',
    style: '',
    optionStyle: '',
    remark: '',
  })
}

// 提交表单
const handleSubmit = async () => {
  try {
    formRef.value?.validate()
    loading.value = true

    // 处理 routeQuery、style、optionStyle 字段（字符串转对象）
    let routeQuery: Record<string, any> | undefined
    if (form.routeQuery?.trim()) {
      try {
        routeQuery = JSON.parse(form.routeQuery)
      } catch (_e) {
        message.error(t('system.function.routeQueryFormatError'))
        return
      }
    }

    let style: Record<string, any> | undefined
    if (form.style?.trim()) {
      try {
        style = JSON.parse(form.style)
      } catch (_e) {
        message.error(t('system.function.styleFormatError'))
        return
      }
    }

    let optionStyle: Record<string, any> | undefined
    if (form.optionStyle?.trim()) {
      try {
        optionStyle = JSON.parse(form.optionStyle)
      } catch (_e) {
        message.error(t('system.function.optionStyleFormatError'))
        return
      }
    }

    // 构建原始数据对象
    const rawData: any = {
      parentId: form.parentId,
      functionName: form.functionName,
      functionKey: form.functionKey,
      functionType: form.functionType,
      scene: form.scene,
      routePath: form.routePath,
      routeCache: form.routeCache,
      routeExternal: form.routeExternal,
      routeQuery,
      component: form.component,
      layoutComponent: form.layoutComponent,
      icon: form.icon,
      sortOrder: form.sortOrder,
      visible: form.visible,
      status: form.status,
      style,
      optionStyle,
      remark: form.remark,
    }

    // 根据功能类型过滤字段
    const filteredData = filterFieldsByType(form.functionType, rawData)

    if (isEdit.value) {
      // 修改功能
      const data: FunctionUpdateDTO = {
        functionId: props.functionId!,
        ...filteredData,
      }
      const res = await updateFunction(data)
      if (res.code === 200) {
        message.success(t('common.updateSuccess'))
        emit('success')
      }
    } else {
      // 新增功能
      const data: FunctionCreateDTO = {
        ...filteredData,
      }
      const res = await addFunction(data)
      if (res.code === 200) {
        message.success(t('common.addSuccess'))
        emit('success')
      }
    }
  } catch (error: any) {
    if (error.errorFields) {
      // 表单验证失败
      return
    }
    message.error(isEdit.value ? t('common.updateFailed') : t('common.addFailed'))
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  emit('update:visible', false)
}

// 监听弹窗显示
watch(
  () => props.visible,
  (val) => {
    if (val) {
      getFunctionTree()
      if (isEdit.value) {
        getFunctionInfo()
      } else {
        resetForm()
      }
    } else {
      resetForm()
    }
  }
)

// 监听父级ID变化
watch(
  () => props.parentId,
  (val) => {
    if (val !== undefined && !isEdit.value) {
      form.parentId = val
    }
  }
)
</script>

<style scoped>
.form-item-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
  line-height: 1.4;
}
</style>
