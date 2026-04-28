<template>
  <a-modal
    :open="visible"
    :title="title"
    :confirm-loading="loading"
    width="600px"
    @ok="handleSubmit"
    @cancel="handleCancel"
  >
    <a-form ref="formRef" :model="formData" :rules="rules as any" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
      <a-form-item v-if="formData.parentId !== 0" :label="t('system.dept.parentDept')" name="parentId">
        <a-tree-select
          v-model:value="formData.parentId"
          :tree-data="deptOptions"
          :field-names="{ label: 'deptName', value: 'deptId', children: 'children' }"
          :placeholder="t('system.dept.parentDeptPlaceholder')"
          tree-default-expand-all
          allow-clear
          show-search
          :filter-tree-node="(input: string, node: any) => node.deptName.toLowerCase().includes(input.toLowerCase())"
        />
      </a-form-item>
      <a-form-item :label="t('system.dept.deptName')" name="deptName">
        <a-input v-model:value="formData.deptName" :placeholder="t('system.dept.deptNamePlaceholder')" />
      </a-form-item>
      <a-form-item :label="t('system.dept.deptKey')" name="deptKey">
        <a-input v-model:value="formData.deptKey" :placeholder="t('system.dept.deptKeyPlaceholder')" />
      </a-form-item>
      <a-form-item :label="t('common.sortDisplay')" name="sortOrder">
        <a-input-number v-model:value="formData.sortOrder" :min="0" style="width: 100%" />
      </a-form-item>
      <a-form-item :label="t('system.dept.leader')" name="leader">
        <a-input v-model:value="formData.leader" :placeholder="t('system.dept.leaderPlaceholder')" :maxlength="20" />
      </a-form-item>
      <a-form-item :label="t('system.dept.phone')" name="phone">
        <a-input v-model:value="formData.phone" :placeholder="t('system.dept.phonePlaceholder')" :maxlength="11" />
      </a-form-item>
      <a-form-item :label="t('common.email')" name="email">
        <a-input v-model:value="formData.email" :placeholder="t('common.emailPlaceholder')" :maxlength="50" />
      </a-form-item>
      <a-form-item :label="t('common.status')" name="status">
        <DictRadio v-model:model-value="formData.status" dict-type="sys_data_status" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import type { FormInstance } from 'ant-design-vue'
import { addDept, updateDept, getDeptList, getDeptExcludeTree } from '@/api/system/dept.ts'
import type { DeptCreateDTO, DeptUpdateDTO, DeptTreeVO } from '@/types/api/system/dept.ts'
import DictRadio from '../../../../../components/dict/DictRadio.vue'

const { t } = useI18n()

interface Props {
  visible: boolean
  deptId?: number
  parentId?: number
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const loading = ref(false)
const deptOptions = ref<DeptTreeVO[]>([])

const title = computed(() => {
  if (props.deptId) return t('system.dept.editDept')
  if (props.parentId && props.parentId !== 0) return t('system.dept.addChildDept')
  return t('system.dept.addDept')
})

const formData = reactive<DeptCreateDTO & { deptId?: number }>({
  deptId: undefined,
  parentId: 0,
  deptName: '',
  deptKey: '',
  leader: undefined,
  phone: undefined,
  email: undefined,
  status: '0',
  sortOrder: 0,
})

const rules = {
  deptName: [{ required: true, message: t('system.dept.deptNameRequired'), trigger: 'blur' }],
  deptKey: [{ required: true, message: t('system.dept.deptKeyRequired'), trigger: 'blur' }],
  sortOrder: [{ required: true, message: t('common.sortRequired'), trigger: 'blur' }],
  email: [{ type: 'email', message: t('system.user.emailFormatInvalid'), trigger: ['blur', 'change'] }],
  phone: [{ pattern: /^1[3456789][0-9]\d{8}$/, message: t('system.user.phonenumberFormatInvalid'), trigger: 'blur' }],
}

// 构建树形结构
const buildTree = (list: DeptTreeVO[]): DeptTreeVO[] => {
  const map = new Map<number, DeptTreeVO>()
  const tree: DeptTreeVO[] = []

  // 先创建映射
  list.forEach((item) => {
    map.set(item.deptId, { ...item, children: [] })
  })

  // 构建树
  list.forEach((item) => {
    const node = map.get(item.deptId)!
    if (item.parentId === 0) {
      tree.push(node)
    } else {
      const parent = map.get(item.parentId)
      if (parent) {
        parent.children ??= []
        parent.children.push(node)
      }
    }
  })

  return tree
}

// 重置表单
const resetForm = () => {
  formData.deptId = undefined
  formData.parentId = props.parentId || 0
  formData.deptName = ''
  formData.deptKey = ''
  formData.leader = undefined
  formData.phone = undefined
  formData.email = undefined
  formData.status = '0'
  formData.sortOrder = 0
  formRef.value?.resetFields()
}

// 获取部门树选项
const getDeptTreeOptions = async (excludeId?: number) => {
  try {
    const res = excludeId ? await getDeptExcludeTree(excludeId) : await getDeptList()
    if (res.code === 200) {
      deptOptions.value = buildTree(res.data || [])
    }
  } catch (_e) {
    message.error(t('common.getDeptTreeFailed'))
  }
}

// 监听 visible 变化
watch(
  () => props.visible,
  async (val) => {
    if (val) {
      if (props.deptId) {
        // 编辑模式：获取排除当前部门及其子部门的树
        await getDeptTreeOptions(props.deptId)
        // 设置表单数据
        const dept = deptOptions.value
          .flatMap((node) => [node, ...(node.children || [])])
          .find((d) => d.deptId === props.deptId)
        if (dept) {
          Object.assign(formData, {
            deptId: dept.deptId,
            parentId: dept.parentId,
            deptName: dept.deptName,
            deptKey: dept.deptKey,
            leader: dept.leader,
            phone: dept.phone,
            email: dept.email,
            status: dept.status,
            sortOrder: dept.sortOrder,
          })
        }
      } else {
        // 新增模式
        await getDeptTreeOptions()
        resetForm()
      }
    } else {
      resetForm()
    }
  }
)

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    let res
    if (formData.deptId) {
      // 修改
      const updateData: DeptUpdateDTO = {
        deptId: formData.deptId,
        parentId: formData.parentId,
        deptName: formData.deptName,
        deptKey: formData.deptKey,
        leader: formData.leader,
        phone: formData.phone,
        email: formData.email,
        status: formData.status,
        sortOrder: formData.sortOrder,
      }
      res = await updateDept(updateData)
    } else {
      // 新增
      const createData: DeptCreateDTO = {
        parentId: formData.parentId,
        deptName: formData.deptName,
        deptKey: formData.deptKey,
        leader: formData.leader,
        phone: formData.phone,
        email: formData.email,
        status: formData.status,
        sortOrder: formData.sortOrder,
      }
      res = await addDept(createData)
    }

    if (res.code === 200) {
      message.success(formData.deptId ? t('common.updateSuccess') : t('common.addSuccess'))
      emit('success')
      handleCancel()
    }
  } catch (error: any) {
    if (error.errorFields) {
      // 表单验证失败
      return
    }
    message.error(t('common.failed'))
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
