<template>
  <div class="user-management">
    <!-- 左侧部门树 -->
    <div class="dept-sidebar" :class="{ collapsed: deptCollapsed }">
      <a-card :bordered="false" class="dept-card">
        <template #title>
          <span>{{ t('system.user.deptList') }}</span>
        </template>
        <template #extra>
          <a-input-search
            v-model:value="deptName"
            :placeholder="t('system.user.searchDept')"
            style="width: 120px"
            allow-clear
            @search="filterDeptTree"
          />
        </template>
        <a-tree
          ref="deptTreeRef"
          :tree-data="deptOptions as any"
          :field-names="{ key: 'deptId', title: 'deptName', children: 'children' }"
          :filter-tree-node="filterNode as any"
          default-expand-all
          @select="handleDeptSelect"
        />
      </a-card>
    </div>

    <!-- 折叠按钮 -->
    <div class="dept-collapse-btn" :class="{ collapsed: deptCollapsed }" @click="deptCollapsed = !deptCollapsed">
      <LeftOutlined v-if="!deptCollapsed" />
      <RightOutlined v-else />
    </div>

    <!-- 右侧表格区域 -->
    <div class="table-area">
      <TablePageLayout>
        <!-- 搜索表单 -->
        <template #search>
          <a-card :bordered="false">
            <a-form layout="inline" :model="queryParams">
              <a-form-item :label="t('common.userName')">
                <a-input
                  v-model:value="queryParams.userName"
                  :placeholder="t('common.userNamePlaceholder')"
                  allow-clear
                  style="width: 200px"
                  @press-enter="handleQuery"
                />
              </a-form-item>
              <a-form-item :label="t('system.user.phonenumber')">
                <a-input
                  v-model:value="queryParams.phonenumber"
                  :placeholder="t('system.user.phonenumberPlaceholder')"
                  allow-clear
                  style="width: 200px"
                  @press-enter="handleQuery"
                />
              </a-form-item>
              <a-form-item :label="t('common.status')">
                <DictSelect
                  v-model:model-value="queryParams.status"
                  dict-type="sys_data_status"
                  :placeholder="t('system.user.statusPlaceholder')"
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

        <!-- 操作按钮 -->
        <template #actions>
          <a-space>
            <a-button type="primary" @click="handleAdd">
              <template #icon><PlusOutlined /></template>
              {{ t('common.add') }}
            </a-button>
            <a-button type="default" :disabled="single" @click="handleUpdate">
              <template #icon><EditOutlined /></template>
              {{ t('common.edit') }}
            </a-button>
            <a-button type="default" danger :disabled="multiple" @click="handleDelete">
              <template #icon><DeleteOutlined /></template>
              {{ t('common.delete') }}
            </a-button>
            <a-button type="default" @click="handleImport">
              <template #icon><UploadOutlined /></template>
              {{ t('common.import') }}
            </a-button>
            <a-button type="default" @click="handleExport">
              <template #icon><DownloadOutlined /></template>
              {{ t('common.export') }}
            </a-button>
          </a-space>
        </template>

        <!-- 用户表格 -->
        <template #table="{ scrollY }">
          <a-table
            :columns="columns"
            :data-source="userList"
            :loading="loading"
            :row-selection="rowSelection"
            :pagination="false"
            row-key="userId"
            :scroll="{ x: 1200, y: scrollY }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-switch
                  :checked="record.status === '0'"
                  :checked-children="t('common.normal')"
                  :un-checked-children="t('common.disabled')"
                  @change="(checked: any) => handleStatusChange(record as UserListVO, checked)"
                />
              </template>
              <template v-else-if="column.key === 'studentNo'">
                <span v-if="record.student?.studentNo">{{ record.student.studentNo }}</span>
                <span v-else class="text-gray-400">-</span>
              </template>
              <template v-else-if="column.key === 'teacherNo'">
                <span v-if="record.teacher?.teacherNo">{{ record.teacher.teacherNo }}</span>
                <span v-else class="text-gray-400">-</span>
              </template>
              <template v-else-if="column.key === 'action'">
                <a-space>
                  <a-tooltip :title="t('common.edit')">
                    <a-button type="link" size="small" :disabled="record.userId === 1" @click="handleUpdate(record as UserListVO)">
                      <template #icon><EditOutlined /></template>
                    </a-button>
                  </a-tooltip>
                  <a-tooltip :title="t('common.delete')">
                    <a-button
                      type="link"
                      size="small"
                      danger
                      :disabled="record.userId === 1"
                      @click="handleDelete(record as UserListVO)"
                    >
                      <template #icon><DeleteOutlined /></template>
                    </a-button>
                  </a-tooltip>
                  <a-tooltip :title="t('system.user.resetPassword')">
                    <a-button type="link" size="small" :disabled="record.userId === 1" @click="handleResetPwd(record as UserListVO)">
                      <template #icon><KeyOutlined /></template>
                    </a-button>
                  </a-tooltip>
                  <a-tooltip :title="t('system.user.assignRole')">
                    <a-button type="link" size="small" :disabled="record.userId === 1" @click="handleAuthRole(record as UserListVO)">
                      <template #icon><UserSwitchOutlined /></template>
                    </a-button>
                  </a-tooltip>
                </a-space>
              </template>
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
            :show-total="(total) => `${t('common.total')} ${total} ${t('common.items')}`"
            @change="handlePageChange"
          />
        </template>
      </TablePageLayout>
    </div>

    <!-- 用户表单弹窗 -->
    <UserForm
      v-model:visible="formVisible"
      :user-id="currentUserId"
      :dept-options="enabledDeptOptions"
      @success="handleFormSuccess"
    />

    <!-- 用户角色分配弹窗 -->
    <UserRole v-model:visible="roleVisible" :user-id="currentUserId" @success="handleRoleSuccess" />

    <!-- 重置密码弹窗 -->
    <a-modal
      v-model:open="resetPwdVisible"
      :title="t('system.user.resetPassword')"
      :confirm-loading="resetPwdLoading"
      @ok="handleResetPwdSubmit"
    >
      <a-form :model="resetPwdForm" :label-col="{ span: 6 }">
        <a-form-item :label="t('common.userName')">
          <a-input v-model:value="resetPwdForm.userName" disabled />
        </a-form-item>
        <a-form-item :label="t('system.user.password')" required>
          <a-input-password
            v-model:value="resetPwdForm.password"
            :placeholder="t('common.pleaseInput') + t('system.user.password')"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 导入用户弹窗 -->
    <a-modal v-model:open="importVisible" :title="t('system.user.importUser')" :footer="null" width="600px">
      <a-upload-dragger :before-upload="beforeUpload" :file-list="fileList" @remove="handleRemoveFile">
        <p class="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p class="ant-upload-text">{{ t('common.uploadText') }}</p>
        <p class="ant-upload-hint">{{ t('common.uploadHint') }}</p>
      </a-upload-dragger>
      <div class="mt-4">
        <a-space direction="vertical" style="width: 100%">
          <a-checkbox v-model:checked="uploadUpdateSupport"> {{ t('system.user.importUpdateSupport') }} </a-checkbox>
          <a-button type="link" @click="downloadTemplate">
            <template #icon><DownloadOutlined /></template>
            {{ t('system.user.importTemplate') }}
          </a-button>
          <a-button type="primary" block :loading="uploadLoading" @click="submitImport">
            {{ t('common.startImport') }}
          </a-button>
        </a-space>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  SearchOutlined,
  ReloadOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  DownloadOutlined,
  KeyOutlined,
  UserSwitchOutlined,
  InboxOutlined,
  LeftOutlined,
  RightOutlined,
} from '@ant-design/icons-vue'
import type { TableProps } from 'ant-design-vue'
import type { Key } from 'ant-design-vue/es/_util/type'
import { getUserList, deleteUser, changeUserStatus, resetUserPwd } from '@/api/system/user.ts'
import { getUserDeptTree } from '@/api/system/user.ts'
import { getRoleList } from '@/api/system/role.ts'
import type { UserQueryDTO, UserListVO, UserStatusChangeDTO, UserPasswordResetDTO } from '@/types/api/system/user.ts'
import type { DeptTreeVO } from '@/types/api/system/dept.ts'
import type { RoleListVO } from '@/types/api/system/role.ts'
import { parseTime } from '@/utils/common.ts'
import UserForm from './components/UserForm.vue'
import UserRole from './components/UserRole.vue'
import usePaginationQuery from '@/composables/usePaginationQuery.ts'
import TablePageLayout from '@/layout/TablePageLayout.vue'

const { t } = useI18n()

// 表格列定义
const columns = [
  { title: t('common.userName'), dataIndex: 'userId', key: 'userId', width: 80, fixed: 'left' as const },
  { title: t('common.userName'), dataIndex: 'userName', key: 'userName', width: 120 },
  { title: t('system.user.nickName'), dataIndex: 'nickName', key: 'nickName', width: 120 },
  { title: t('system.user.dept'), dataIndex: 'deptName', key: 'deptName', width: 120 },
  { title: t('system.user.phonenumber'), dataIndex: 'phonenumber', key: 'phonenumber', width: 120 },
  { title: '学号', key: 'studentNo', width: 120 },
  { title: '工号', key: 'teacherNo', width: 120 },
  { title: t('common.status'), dataIndex: 'status', key: 'status', width: 80 },
  { title: t('common.createTime'), dataIndex: 'createTime', key: 'createTime', width: 160 },
  { title: t('common.operation'), key: 'action', fixed: 'right' as const, width: 200 },
]

// 数据状态
const loading = ref(false)
const userList = ref<UserListVO[]>([])
const total = ref(0)
const deptOptions = ref<DeptTreeVO[]>([])
const enabledDeptOptions = ref<DeptTreeVO[]>([])
const roleOptions = ref<RoleListVO[]>([])

// 查询参数的默认值
const defaultQueryParams: UserQueryDTO = {
  page: 1,
  size: 10,
  userName: undefined,
  phonenumber: undefined,
  status: undefined,
  deptIds: undefined,
}

// 临时存储查询参数（在 getList 中使用）
let queryParams: UserQueryDTO = { ...defaultQueryParams }

// 获取用户列表
const getList = async () => {
  loading.value = true
  try {
    const res = await getUserList(queryParams)
    if (res.code === 200) {
      userList.value = res.data.rows ?? []
      total.value = res.data.total || 0
    }
  } catch (_e) {
    message.error(t('common.getUserListFailed'))
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
} = usePaginationQuery<UserQueryDTO>(defaultQueryParams, getList, {
  syncSearchParams: true,
  searchParamKeys: ['userName', 'phonenumber', 'status'],
  debounceUrlUpdate: true,
  debounceDelay: 300,
})

// 使用 hook 返回的 queryParams
queryParams = syncedQueryParams

// 部门树搜索
const deptName = ref('')
const deptTreeRef = ref()
const deptCollapsed = ref(false)

// 选中的行
const selectedRowKeys = ref<number[]>([])
const selectedRows = ref<UserListVO[]>([])
const single = computed(() => selectedRowKeys.value.length !== 1)
const multiple = computed(() => selectedRowKeys.value.length === 0)

// 行选择配置
const rowSelection = computed<TableProps['rowSelection']>(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys, rows) => {
    selectedRowKeys.value = keys as number[]
    selectedRows.value = rows as UserListVO[]
  },
}))

// 弹窗状态
const formVisible = ref(false)
const roleVisible = ref(false)
const resetPwdVisible = ref(false)
const importVisible = ref(false)

// 当前操作的用户
const currentUserId = ref<number>()

// 重置密码表单
const resetPwdLoading = ref(false)
const resetPwdForm = reactive({
  userId: undefined as number | undefined,
  userName: '',
  password: '',
})

// 导入相关
const fileList = ref([])
const uploadUpdateSupport = ref(false)
const uploadLoading = ref(false)

// 获取部门树
const getDeptTree = async () => {
  try {
    const res = await getUserDeptTree()
    if (res.code === 200) {
      deptOptions.value = res.data || []
      enabledDeptOptions.value = res.data || []
    }
  } catch (_e) {
    message.error(t('common.getDeptTreeFailed'))
  }
}

// 获取角色列表
const getRoles = async () => {
  try {
    const res = await getRoleList({ page: 1, size: 100 })
    if (res.code === 200) {
      roleOptions.value = res.data.rows ?? []
    }
  } catch (_e) {
    message.error(t('common.getRoleListFailed'))
  }
}

// 搜索用户
const handleQuery = () => {
  queryParams.page = 1
  getList()
}

// 重置查询
const resetQuery = () => {
  resetAll()
  deptName.value = ''
  // resetAll 会重置所有参数并清空 URL，但需要手动触发一次获取
  fetch()
}

// 部门树筛选
const filterNode = (node: DeptTreeVO) => {
  if (!deptName.value) return true
  return node.deptName.toLowerCase().includes(deptName.value.toLowerCase())
}

const filterDeptTree = () => {
  // 触发树过滤
}

// 点击部门节点
const handleDeptSelect = (selectedKeys: (string | number)[]) => {
  if (selectedKeys.length > 0) {
    queryParams.deptIds = [selectedKeys[0] as number]
  } else {
    queryParams.deptIds = undefined
  }
  getList()
}

// 分页变化
const handlePageChange = () => {
  getList()
}

// 新增用户
const handleAdd = () => {
  currentUserId.value = undefined
  formVisible.value = true
}

// 修改用户
const handleUpdate = (record?: any) => {
  if (record?.userId) {
    currentUserId.value = record.userId
  } else if (selectedRows.value.length === 1) {
    currentUserId.value = selectedRows.value[0]?.userId
  }
  formVisible.value = true
}

// 删除用户
const handleDelete = (record?: any) => {
  let userIds: string
  if (record) {
    userIds = String(record.userId)
  } else {
    userIds = selectedRowKeys.value.join(',')
  }

  Modal.confirm({
    title: t('common.systemTip'),
    content: record ? t('common.confirmDelete', { target: t('common.this') }) : t('common.confirmDeleteSelected'),
    onOk: async () => {
      try {
        const res = await deleteUser(userIds)
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
const handleStatusChange = async (record: UserListVO, checked: boolean) => {
  const data: UserStatusChangeDTO = {
    userId: record.userId,
    status: checked ? '0' : '1',
  }
  try {
    const res = await changeUserStatus(data)
    if (res.code === 200) {
      message.success(t('common.statusChangeSuccess'))
      getList()
    }
  } catch (_e) {
    message.error(t('common.statusChangeFailed'))
  }
}

// 重置密码
const handleResetPwd = (record: UserListVO) => {
  resetPwdForm.userId = record.userId
  resetPwdForm.userName = record.userName
  resetPwdForm.password = ''
  resetPwdVisible.value = true
}

const handleResetPwdSubmit = async () => {
  if (!resetPwdForm.password) {
    message.warning(t('common.pleaseEnterNewPassword'))
    return
  }

  resetPwdLoading.value = true
  try {
    const data: UserPasswordResetDTO = {
      userId: resetPwdForm.userId!,
      password: resetPwdForm.password,
    }
    const res = await resetUserPwd(data)
    if (res.code === 200) {
      message.success(t('common.resetPasswordSuccess'))
      resetPwdVisible.value = false
    }
  } catch (_e) {
    message.error(t('common.resetPasswordFailed'))
  } finally {
    resetPwdLoading.value = false
  }
}

// 分配角色
const handleAuthRole = (record: UserListVO) => {
  currentUserId.value = record.userId
  roleVisible.value = true
}

// 导入用户
const handleImport = () => {
  importVisible.value = true
}

// 导出用户
const handleExport = () => {
  message.info(t('common.exportFeatureInDevelopment'))
}

// 下载模板
const downloadTemplate = () => {
  message.info(t('common.templateDownloadInDevelopment'))
}

// 上传前校验
const beforeUpload = (file: File) => {
  const isExcel =
    file.type === 'application/vnd.ms-excel' ||
    file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  if (!isExcel) {
    message.error(t('common.onlyUploadExcel'))
    return false
  }
  fileList.value = [file as any] as any
  return false
}

// 移除文件
const handleRemoveFile = () => {
  fileList.value = []
}

// 提交导入
const submitImport = () => {
  if (fileList.value.length === 0) {
    message.warning(t('common.pleaseSelectFile'))
    return
  }
  message.info(t('common.importFeatureInDevelopment'))
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

// 角色分配成功
const handleRoleSuccess = () => {
  roleVisible.value = false
  getList()
}

// 监听部门名称变化
watch(deptName, (_val) => {
  if (deptTreeRef.value) {
    deptTreeRef.value.filter()
  }
})

// 初始化
onMounted(() => {
  getList()
  getDeptTree()
  getRoles()
})
</script>

<style scoped>
@reference "#main.css";

.user-management {
  height: 100%;
  display: flex;
  padding: 10px;
  gap: 10px;
  position: relative;
}

.dept-sidebar {
  width: 260px;
  flex-shrink: 0;
  overflow: hidden;
  transition: width 0.3s cubic-bezier(0.2, 0, 0, 1);
}

.dept-sidebar.collapsed {
  width: 0;
}

.dept-card {
  height: 100%;
  width: 260px;
  overflow-y: auto;

  :deep(.ant-card-body) {
    padding: 16px;
  }
}

.dept-collapse-btn {
  @apply flex items-center justify-center cursor-pointer
    bg-white dark:bg-gray-800
    border border-gray-200 dark:border-gray-600
    rounded-r-md
    text-gray-400 hover:text-primary dark:text-gray-500 dark:hover:text-primary
    shadow-sm hover:shadow
    transition-all duration-200;
  position: absolute;
  top: 50%;
  left: 260px;
  transform: translateY(-50%);
  z-index: 10;
  width: 16px;
  height: 48px;
  margin-left: -1px;
  transition:
    left 0.3s cubic-bezier(0.2, 0, 0, 1),
    color 0.2s,
    box-shadow 0.2s;
}

.dept-collapse-btn.collapsed {
  left: 10px;
}

.table-area {
  flex: 1;
  min-width: 0;
  overflow: hidden;

  :deep(.table-page-layout) {
    padding: 0;
  }
}
</style>
