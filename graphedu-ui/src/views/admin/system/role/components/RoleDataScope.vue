<template>
  <a-modal
    :open="visible"
    :title="t('system.role.assignDataScope')"
    :confirm-loading="loading"
    :width="600"
    @cancel="handleCancel"
    @ok="handleSubmit"
  >
    <a-form ref="formRef" :model="form" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
      <a-form-item :label="t('system.role.roleName')">
        <a-input v-model:value="form.roleName" disabled />
      </a-form-item>

      <a-form-item :label="t('system.role.roleKey')">
        <a-input v-model:value="form.roleKey" disabled />
      </a-form-item>

      <a-form-item :label="t('system.role.dataScope')" name="dataScope">
        <a-select
          v-model:value="form.dataScope"
          :placeholder="t('system.role.dataScopePlaceholder')"
          @change="handleDataScopeChange"
        >
          <a-select-option value="1">{{ t('system.role.dataScopeAllPermission') }}</a-select-option>
          <a-select-option value="2">{{ t('system.role.dataScopeCustom') }}</a-select-option>
          <a-select-option value="3">{{ t('system.role.dataScopeDeptPermission') }}</a-select-option>
          <a-select-option value="4">{{ t('system.role.dataScopeDeptAndChildPermission') }}</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item v-if="form.dataScope === '2'" :label="t('system.role.dataPermission')" name="deptIds">
        <div class="tree-actions">
          <a-checkbox v-model:checked="expandAll" @change="(e: any) => handleExpandAll(e.target.checked)">{{
            t('common.expandCollapse')
          }}</a-checkbox>
          <a-checkbox v-model:checked="checkAll" @change="(e: any) => handleCheckAll(e.target.checked)">{{ t('system.role.selectAll') }}</a-checkbox>
          <a-checkbox v-model:checked="checkStrictly">{{ t('system.role.parentChildLinkage') }}</a-checkbox>
        </div>
        <a-spin :spinning="treeLoading">
          <a-tree
            ref="treeRef"
            v-model:checked-keys="form.deptIds"
            :tree-data="deptTreeData as any"
            :field-names="{ key: 'deptId', title: 'deptName', children: 'children' }"
            :checkable="true"
            :check-strictly="!checkStrictly"
            :expanded-keys="expandedKeys"
            :auto-expand-parent="autoExpandParent"
            :selectable="false"
            default-expand-all
          />
        </a-spin>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import type { FormInstance } from 'ant-design-vue'
import { getRoleDetail, updateRoleDataScope, getRoleDeptTree } from '@/api/system/role.ts'
import { getDeptList } from '@/api/system/dept.ts'
import type { RoleDatascopeChangeDTO } from '@/types/api/system/role.ts'
import type { RoleDetailVO } from '@/types/api/system/role.ts'
import type { DeptTreeVO } from '@/types/api/system/dept.ts'

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
const deptTreeData = ref<DeptTreeVO[]>([])

// 树展开相关
const expandAll = ref(false)
const expandedKeys = ref<number[]>([])
const autoExpandParent = ref(true)

// 树选择相关
const checkAll = ref(false)
const checkStrictly = ref(false)

// 表单数据
const form = reactive<Partial<RoleDatascopeChangeDTO> & { roleName?: string; roleKey?: string }>({
  roleId: undefined,
  roleName: '',
  roleKey: '',
  dataScope: '1',
  deptIds: [],
})

// 获取部门树
const getDeptTree = async () => {
  treeLoading.value = true
  try {
    const res = await getDeptList()
    if (res.code === 200) {
      deptTreeData.value = res.data || []
    }
  } catch (_e) {
    message.error(t('common.getDeptTreeFailed'))
  } finally {
    treeLoading.value = false
  }
}

// 获取角色详情和已分配的部门
const getRoleInfo = async () => {
  if (!props.roleId) return

  loading.value = true
  try {
    // 并行获取角色详情和已分配的部门权限
    const [roleRes, deptRes] = await Promise.all([getRoleDetail(props.roleId), getRoleDeptTree(props.roleId)])

    if (roleRes.code === 200) {
      const role = roleRes.data
      form.roleId = role.roleId
      form.roleName = role.roleName
      form.roleKey = role.roleKey
      form.dataScope = role.dataScope as any
      form.deptIds = deptRes.data?.checkedIds || []
    }
  } catch (_e) {
    message.error(t('system.role.getRoleInfoFailed'))
  } finally {
    loading.value = false
  }
}

// 展开/折叠所有
const handleExpandAll = (checked: boolean) => {
  if (checked) {
    // 展开所有节点
    const getAllKeys = (tree: DeptTreeVO[]): number[] => {
      const keys: number[] = []
      tree.forEach((node) => {
        keys.push(node.deptId)
        if (node.children && node.children.length > 0) {
          keys.push(...getAllKeys(node.children))
        }
      })
      return keys
    }
    expandedKeys.value = getAllKeys(deptTreeData.value)
  } else {
    expandedKeys.value = []
  }
  autoExpandParent.value = false
}

// 全选/全不选
const handleCheckAll = (checked: boolean) => {
  if (checked) {
    // 获取所有节点的 key
    const getAllKeys = (tree: DeptTreeVO[]): number[] => {
      const keys: number[] = []
      tree.forEach((node) => {
        keys.push(node.deptId)
        if (node.children && node.children.length > 0) {
          keys.push(...getAllKeys(node.children))
        }
      })
      return keys
    }
    form.deptIds = getAllKeys(deptTreeData.value)
  } else {
    form.deptIds = []
  }
}

// 数据范围变化
const handleDataScopeChange = (value: any) => {
  if (value !== '2') {
    // 非自定数据权限时，清空已选择的部门
    form.deptIds = []
  }
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(form, {
    roleId: undefined,
    roleName: '',
    roleKey: '',
    dataScope: '1',
    deptIds: [],
  })
  expandAll.value = false
  checkAll.value = false
  checkStrictly.value = false
  expandedKeys.value = []
}

// 提交表单
const handleSubmit = async () => {
  if (!props.roleId) {
    message.warning(t('system.role.roleIdRequired'))
    return
  }

  loading.value = true
  try {
    const data: RoleDatascopeChangeDTO = {
      roleId: props.roleId,
      dataScope: form.dataScope!,
      deptIds: form.deptIds as number[],
    }
    const res = await updateRoleDataScope(data)
    if (res.code === 200) {
      message.success(t('common.updateSuccess'))
      emit('success')
    }
  } catch (_e) {
    message.error(t('common.updateFailed'))
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
      getDeptTree()
      if (props.roleId) {
        getRoleInfo()
      }
    } else {
      resetForm()
    }
  }
)
</script>

<style scoped>
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
