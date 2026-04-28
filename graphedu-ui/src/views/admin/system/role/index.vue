<template>
  <TablePageLayout>
    <!-- 搜索表单 -->
    <template #search>
      <a-card :bordered="false">
        <a-form layout="inline" :model="queryParams">
          <a-form-item :label="t('system.role.roleName')">
            <a-input
              v-model:value="queryParams.roleName"
              :placeholder="t('system.role.roleNamePlaceholder')"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item :label="t('system.role.roleKey')">
            <a-input
              v-model:value="queryParams.roleKey"
              :placeholder="t('system.role.roleKeyPlaceholder')"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item :label="t('common.status')">
            <DictSelect
              v-model:model-value="queryParams.status"
              dict-type="sys_data_status"
              :placeholder="t('system.role.statusPlaceholder')"
              allow-clear
              style="width: 150px"
            />
          </a-form-item>
          <a-form-item>
            <a-space>
              <a-button type="primary" @click="handleQuery">
                <template #icon><SearchOutlined /></template>
                {{ t('common.search') }}
              </a-button>
              <a-button @click="resetQuery">
                <template #icon><ReloadOutlined /></template>
                {{ t('common.reset') }}
              </a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </a-card>
    </template>

    <!-- 操作按钮和表格 -->
    <!-- 操作按钮 -->
    <template #actions>
      <a-space>
        <a-button type="primary" @click="handleAdd">
          <template #icon><PlusOutlined /></template>
          {{ t('common.add') }}
        </a-button>
        <a-button type="default" :disabled="single" @click="() => handleUpdate()">
          <template #icon><EditOutlined /></template>
          {{ t('common.edit') }}
        </a-button>
        <a-button type="default" danger :disabled="multiple" @click="() => handleDelete()">
          <template #icon><DeleteOutlined /></template>
          {{ t('common.delete') }}
        </a-button>
        <a-button type="default" @click="handleExport">
          <template #icon><DownloadOutlined /></template>
          {{ t('common.export') }}
        </a-button>
      </a-space>
    </template>

    <!-- 角色表格 -->
    <template #table="{ scrollY }">
      <a-table
        :columns="columns"
        :data-source="roleList"
        :loading="loading"
        :row-selection="rowSelection"
        :pagination="false"
        row-key="roleId"
        :scroll="{ x: 'max-content', y: scrollY }"
      >
        <!-- 状态列 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-switch
              :checked="record.status === '0'"
              :checked-children="t('common.normal')"
              :un-checked-children="t('common.disabled')"
              :disabled="record.roleId <= 10"
              @change="(checked: any) => handleStatusChange(record as RoleListVO, checked)"
            />
          </template>
          <!-- 数据范围列 -->
          <template v-else-if="column.key === 'dataScope'">
            <DictTag :options="sys_role_data_scope" :value="record.dataScope" />
          </template>
          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-tooltip :title="t('common.edit')">
                <a-button type="link" size="small" :disabled="record.roleId <= 10" @click="handleUpdate(record as RoleListVO)">
                  <template #icon><EditOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip :title="t('common.delete')">
                <a-button type="link" size="small" danger :disabled="record.roleId <= 10" @click="handleDelete(record as RoleListVO)">
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip :title="t('system.role.assignDataScope')">
                <a-button type="link" size="small" :disabled="record.roleId <= 10" @click="handleDataScope(record as RoleListVO)">
                  <template #icon><SafetyOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip :title="t('system.role.assignUser')">
                <a-button type="link" size="small" :disabled="record.roleId <= 10" @click="handleAuthUser(record as RoleListVO)">
                  <template #icon><UserOutlined /></template>
                </a-button>
              </a-tooltip>
            </a-space>
          </template>
          <!-- 时间列 -->
          <template v-else-if="column.key === 'createTime'">
            {{ formatTime(record.createTime) }}
          </template>
        </template>
      </a-table>
    </template>

    <!-- 分页 -->
    <template #pagination>
      <a-pagination
        v-model:current="queryParams.page"
        v-model:page-size="queryParams.size"
        :total="total"
        :show-size-changer="true"
        :show-total="showTotal"
        @change="handlePageChange"
      />
    </template>
  </TablePageLayout>
  <!-- 角色表单弹窗 -->
  <RoleForm v-model:visible="formVisible" :role-id="currentRoleId" @success="handleFormSuccess" />
  <!-- 数据权限分配弹窗 -->
  <RoleDataScope v-model:visible="dataScopeVisible" :role-id="currentRoleId" @success="handleDataScopeSuccess" />
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  SearchOutlined,
  ReloadOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  DownloadOutlined,
  SafetyOutlined,
  UserOutlined,
} from '@ant-design/icons-vue'
import type { TableProps } from 'ant-design-vue'
import { getRoleList, deleteRole, changeRoleStatus } from '@/api/system/role.ts'
import type { RoleQueryDTO, RoleListVO, RoleStatusChangeDTO } from '@/types/api/system/role.ts'
import RoleForm from './components/RoleForm.vue'
import RoleDataScope from './components/RoleDataScope.vue'
import TablePageLayout from '@/layout/TablePageLayout.vue'
import { useDict } from '@/utils/dict.ts'
import { parseTime } from '@/utils/common.ts'
import usePaginationQuery from '@/composables/usePaginationQuery.ts'

const { t } = useI18n()

// 数据范围映射
const { sys_role_data_scope } = useDict('sys_role_data_scope')

// 表格列定义
const columns: TableProps['columns'] = [
  { title: t('system.role.roleName'), dataIndex: 'roleId', key: 'roleId', width: 100, fixed: 'left' as const },
  { title: t('system.role.roleName'), dataIndex: 'roleName', key: 'roleName', width: 150 },
  { title: t('system.role.roleKey'), dataIndex: 'roleKey', key: 'roleKey', width: 150 },
  { title: t('common.displayOrder'), dataIndex: 'roleSort', key: 'roleSort', width: 100 },
  { title: t('system.role.dataScope'), dataIndex: 'dataScope', key: 'dataScope', width: 180 },
  { title: t('common.status'), dataIndex: 'status', key: 'status', width: 100 },
  { title: t('common.createTime'), dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: t('common.operation'), key: 'action', fixed: 'right' as const, width: 200 },
]

// 数据状态
const loading = ref(false)
const roleList = ref<RoleListVO[]>([])
const total = ref(0)

// 查询参数的默认值
const defaultQueryParams: RoleQueryDTO = {
  page: 1,
  size: 10,
  roleName: undefined,
  roleKey: undefined,
  status: undefined,
}

// 临时存储查询参数（在 getList 中使用）
let queryParams: RoleQueryDTO = { ...defaultQueryParams }

// 获取角色列表
const getList = async () => {
  loading.value = true
  try {
    const res = await getRoleList(queryParams)
    if (res.code === 200) {
      roleList.value = res.data.rows || []
      total.value = res.data.total || 0
    }
  } catch (_e) {
    message.error(t('common.getRoleListFailed'))
  } finally {
    loading.value = false
  }
}

// 使用 usePaginationQuery Hook 管理查询参数
const {
  queryParams: syncedQueryParams,
  resetPage,
  resetAll,
  fetch,
} = usePaginationQuery<RoleQueryDTO>(defaultQueryParams, getList, {
  syncSearchParams: true,
  searchParamKeys: ['roleName', 'roleKey', 'status'],
  debounceUrlUpdate: true,
  debounceDelay: 300,
})

// 使用 hook 返回的 queryParams
queryParams = syncedQueryParams

// 选中的行
const selectedRowKeys = ref<number[]>([])
const selectedRows = ref<RoleListVO[]>([])
const single = computed(() => selectedRowKeys.value.length !== 1)
const multiple = computed(() => selectedRowKeys.value.length === 0)

// 行选择配置
const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: (string | number)[], rows: any[]) => {
    selectedRowKeys.value = keys as number[]
    selectedRows.value = rows as RoleListVO[]
  },
  getCheckboxProps: (record: RoleListVO) => ({
    disabled: record.roleId <= 10,
  }),
}))

// 弹窗状态
const formVisible = ref(false)
const dataScopeVisible = ref(false)

// 当前操作的角色
const currentRoleId = ref<number>()

// 搜索角色
const handleQuery = () => {
  queryParams.page = 1
  getList()
}

// 重置查询
const resetQuery = () => {
  resetAll()
  fetch()
}

// 分页变化
const handlePageChange = () => {
  getList()
}

// 新增角色
const handleAdd = () => {
  currentRoleId.value = undefined
  formVisible.value = true
}

// 修改角色
const handleUpdate = (record?: RoleListVO) => {
  if (record) {
    currentRoleId.value = record.roleId
  } else if (selectedRows.value.length === 1) {
    currentRoleId.value = selectedRows.value[0]?.roleId
  }
  formVisible.value = true
}

// 删除角色
const handleDelete = (record?: RoleListVO) => {
  let roleIds: string
  if (record) {
    roleIds = String(record.roleId)
  } else {
    roleIds = selectedRowKeys.value.join(',')
  }

  Modal.confirm({
    title: t('common.systemTip'),
    content: record ? t('system.role.deleteRoleConfirm', { roleName: record.roleName }) : t('common.deleteConfirm'),
    onOk: async () => {
      try {
        const res = await deleteRole(roleIds)
        if (res.code === 200) {
          message.success(t('common.deleteSuccess'))
          getList()
        }
      } catch (_e) {
        message.error(t('common.deleteFailed'))
      }
    },
  })
}

// 状态变更
const handleStatusChange = async (record: RoleListVO, checked: boolean) => {
  const data: RoleStatusChangeDTO = {
    roleId: record.roleId,
    status: checked ? '0' : '1',
  }
  try {
    const res = await changeRoleStatus(data)
    if (res.code === 200) {
      message.success(t('system.role.roleStatusChangeSuccess'))
      getList()
    }
  } catch (_e) {
    message.error(t('system.role.roleStatusChangeFailed'))
  }
}

// 分页组件的 show-total 回调
const showTotal = (total: number) => `${t('common.total')} ${total} ${t('common.items')}`

// 分配数据权限
const handleDataScope = (record: RoleListVO) => {
  currentRoleId.value = record.roleId
  dataScopeVisible.value = true
}

// 分配用户
const handleAuthUser = (_record: RoleListVO) => {
  message.info('用户分配功能开发中')
  // TODO: 跳转到用户分配页面
}

// 导出角色
const handleExport = () => {
  message.info('导出功能开发中')
}

// 格式化时间
const formatTime = (time: string | undefined) => {
  if (!time) return ''
  return parseTime(time)
}

// 表单提交成功
const handleFormSuccess = () => {
  formVisible.value = false
  getList()
}

// 数据权限分配成功
const handleDataScopeSuccess = () => {
  dataScopeVisible.value = false
  getList()
}

// 初始化
onMounted(() => {
  getList()
})
</script>
