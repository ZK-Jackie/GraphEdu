<template>
  <a-modal
    :open="visible"
    :title="title"
    :confirm-loading="loading"
    :width="600"
    @cancel="handleCancel"
    @ok="handleSubmit"
  >
    <a-spin :spinning="loading" :tip="t('common.loading')">
      <a-form ref="formRef" :model="form" :rules="rules as any" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item :label="t('system.role.roleName')" name="roleName">
          <a-input v-model:value="form.roleName" :placeholder="t('system.role.roleNamePlaceholder')" :maxlength="30" />
        </a-form-item>

        <a-form-item :label="t('system.role.roleKey')" name="roleKey">
          <a-input v-model:value="form.roleKey" :placeholder="t('system.role.roleKeyPlaceholder')" :maxlength="30" />
          <div class="form-item-tip">{{ t('system.role.roleKeyTip') }}</div>
        </a-form-item>

        <a-form-item :label="t('common.status')" name="status">
          <DictRadio v-model:model-value="form.status" dict-type="sys_data_status" />
        </a-form-item>

        <a-form-item :label="t('system.role.dataScope')" name="dataScope">
          <DictSelect
            v-model:model-value="form.dataScope"
            dict-type="sys_role_data_scope"
            :placeholder="t('system.role.dataScopePlaceholder')"
            allow-clear
          />
        </a-form-item>

        <a-form-item :label="t('system.role.functionPermission')">
          <div class="tree-actions">
            <a-checkbox v-model:checked="expandAll" @change="(e: any) => handleExpandAll(e.target.checked)">{{
              t('common.expandCollapse')
            }}</a-checkbox>
            <a-checkbox v-model:checked="checkAll" @change="(e: any) => handleCheckAll(e.target.checked)">{{
              t('system.role.selectAll')
            }}</a-checkbox>
            <a-checkbox v-model:checked="checkStrictly">{{ t('system.role.parentChildLinkage') }}</a-checkbox>
          </div>
          <a-spin :spinning="treeLoading">
            <a-tree
              ref="treeRef"
              v-model:checked-keys="form.functionIds"
              v-model:expanded-keys="expandedKeys"
              :tree-data="functionTreeData as any"
              :field-names="{ key: 'functionId', title: 'functionName', children: 'children' }"
              :checkable="true"
              :check-strictly="!checkStrictly"
              :auto-expand-parent="autoExpandParent"
              :selectable="false"
            />
          </a-spin>
        </a-form-item>

        <a-form-item :label="t('common.remark')" name="remark">
          <a-textarea
            v-model:value="form.remark"
            :placeholder="t('common.remark') + t('common.pleaseInput')"
            :rows="3"
            :maxlength="200"
            show-count
          />
        </a-form-item>
      </a-form>
    </a-spin>
  </a-modal>
</template>

<script setup lang="ts">
import { message } from 'ant-design-vue'
import type { FormInstance } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { addRole, updateRole, getRoleDetail } from '@/api/system/role.ts'
import { getFunctionTreeSelect, getRoleFunctionTree } from '@/api/system/function.ts'
import type { RoleCreateDTO, RoleUpdateDTO } from '@/types/api/system/role.ts'
import type { FunctionTreeVO } from '@/types/api/system/function.ts'
import DictSelect from '../../../../../components/dict/DictSelect.vue'
import DictRadio from '../../../../../components/dict/DictRadio.vue'

const { t } = useI18n()

interface Props {
  visible: boolean
  roleId?: number
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const treeRef = ref<any>()
const loading = ref(false)
const treeLoading = ref(false)
const functionTreeData = ref<FunctionTreeVO[]>([])

// 树展开相关
const expandAll = ref(false)
const expandedKeys = ref<number[]>([])
const autoExpandParent = ref(true)

// 树选择相关
const checkAll = ref(false)
const checkStrictly = ref(false)

// 是否编辑模式
const isEdit = computed(() => !!props.roleId)

// 弹窗标题
const title = computed(() => (isEdit.value ? t('system.role.editRole') : t('system.role.addRole')))

// 表单数据
const form = reactive<Partial<RoleCreateDTO & RoleUpdateDTO>>({
  roleName: '',
  roleKey: '',
  status: '0',
  dataScope: '1',
  functionIds: [],
  remark: '',
})

// 表单验证规则
const rules = {
  roleName: [{ required: true, message: t('system.role.roleNameRequired'), trigger: 'blur' }],
  roleKey: [{ required: true, message: t('system.role.roleKeyRequired'), trigger: 'blur' }],
}

// 获取功能树
const getFunctionTree = async () => {
  treeLoading.value = true
  try {
    const res = await getFunctionTreeSelect()
    if (res.code === 200) {
      functionTreeData.value = (res.data || []) as any
    }
  } catch (_e) {
    message.error(t('system.role.getFunctionTreeFailed'))
  } finally {
    treeLoading.value = false
  }
}

// 获取角色详情（不设置 loading，由调用方控制）
const getRoleInfo = async () => {
  if (!props.roleId) return

  try {
    // 并行获取角色详情和已分配的功能权限
    const [roleRes, functionRes] = await Promise.all([getRoleDetail(props.roleId), getRoleFunctionTree(props.roleId)])

    if (roleRes.code === 200) {
      const role = roleRes.data
      Object.assign(form, {
        roleName: role.roleName,
        roleKey: role.roleKey,
        status: role.status,
        dataScope: role.dataScope,
        functionIds: functionRes.data?.checkedIds || [],
        remark: role.remark,
      })
    }
  } catch (error) {
    message.error(t('system.role.getRoleInfoFailed'))
    throw error // 抛出错误，让外层 catch 处理
  }
}

// 展开/折叠所有
const handleExpandAll = (checked: boolean) => {
  if (checked) {
    // 展开所有节点
    const getAllKeys = (tree: FunctionTreeVO[]): number[] => {
      const keys: number[] = []
      tree.forEach((node) => {
        keys.push(node.functionId)
        if (node.children && node.children.length > 0) {
          keys.push(...getAllKeys(node.children))
        }
      })
      return keys
    }
    expandedKeys.value = getAllKeys(functionTreeData.value)
  } else {
    expandedKeys.value = []
  }
  autoExpandParent.value = false
}

// 全选/全不选
const handleCheckAll = (checked: boolean) => {
  if (checked) {
    // 获取所有节点的 key
    const getAllKeys = (tree: FunctionTreeVO[]): number[] => {
      const keys: number[] = []
      tree.forEach((node) => {
        keys.push(node.functionId)
        if (node.children && node.children.length > 0) {
          keys.push(...getAllKeys(node.children))
        }
      })
      return keys
    }
    form.functionIds = getAllKeys(functionTreeData.value)
  } else {
    form.functionIds = []
  }
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(form, {
    roleName: '',
    roleKey: '',
    status: '0',
    dataScope: '1',
    functionIds: [],
    remark: '',
  })
  expandAll.value = false
  checkAll.value = false
  checkStrictly.value = false
  expandedKeys.value = []
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    if (isEdit.value) {
      // 修改角色
      const data: RoleUpdateDTO = {
        roleId: props.roleId!,
        roleName: form.roleName,
        roleKey: form.roleKey,
        status: form.status,
        dataScope: form.dataScope,
        functionIds: form.functionIds as number[],
        remark: form.remark,
      }
      const res = await updateRole(data)
      if (res.code === 200) {
        message.success(t('common.updateSuccess'))
        emit('success')
      }
    } else {
      // 新增角色
      const data: RoleCreateDTO = {
        roleName: form.roleName!,
        roleKey: form.roleKey!,
        status: form.status,
        dataScope: form.dataScope,
        functionIds: form.functionIds as number[],
        remark: form.remark,
      }
      const res = await addRole(data)
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
  async (val) => {
    if (val) {
      if (isEdit.value) {
        // 编辑模式：立即显示加载状态
        loading.value = true
        try {
          await getFunctionTree()
          await getRoleInfo()
        } catch (_e) {
          // 错误已在各方法内部处理
        } finally {
          loading.value = false
        }
      } else {
        await getFunctionTree()
      }
    } else {
      resetForm()
    }
  }
)
</script>

<style scoped>
.form-item-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.tree-actions {
  margin-bottom: 8px;

  .ant-checkbox-wrapper {
    margin-right: 16px;
  }
}

:deep(.ant-tree) {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  padding: 8px;
}
</style>
