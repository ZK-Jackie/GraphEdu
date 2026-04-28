<template>
  <a-modal
    :open="visible"
    :title="t('system.user.assignRole')"
    :confirm-loading="loading"
    :width="800"
    @cancel="handleCancel"
    @ok="handleSubmit"
  >
    <!-- 用户基本信息 -->
    <a-descriptions :title="t('system.user.basicInfo')" :column="2" bordered size="small">
      <a-descriptions-item :label="t('system.user.nickName')">
        {{ userInfo.nickName }}
      </a-descriptions-item>
      <a-descriptions-item :label="t('system.user.loginAccount')">
        {{ userInfo.userName }}
      </a-descriptions-item>
    </a-descriptions>

    <!-- 角色列表 -->
    <div class="role-section">
      <h4>{{ t('system.user.roleInfo') }}</h4>
      <a-table
        :columns="columns"
        :data-source="roleList"
        :loading="loading"
        :row-selection="rowSelection"
        :pagination="pagination"
        :row-key="(record) => record.roleId"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'createTime'">
            {{ formatTime(record.createTime) }}
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="record.status === '0' ? 'success' : 'default'">
              {{ record.status === '0' ? t('common.normal') : t('common.disabled') }}
            </a-tag>
          </template>
        </template>
      </a-table>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import type { TableProps } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import type { Key } from 'ant-design-vue/es/_util/type'
import type { UserRoleListVO, UserRoleUpdateDTO } from '@/types/api/system/user.ts'
import { getUserRoleList, updateUserRole } from '@/api/system/user.ts'
import { parseTime } from '@/utils/common.ts'

const { t } = useI18n()

interface Props {
  visible: boolean
  userId?: number
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const loading = ref(false)
interface UserInfo {
  userId: number
  userName: string
  nickName?: string
}

const userInfo = ref<UserInfo>({} as UserInfo)
const roleList = ref<any[]>([])
const selectedRoleIds = ref<number[]>([])

// 表格列定义
const columns = [
  { title: '序号', width: 70, customRender: ({ index }: { index: number }) => index + 1 },
  { title: t('system.role.roleName'), dataIndex: 'roleId', key: 'roleId', width: 100 },
  { title: t('system.role.roleName'), dataIndex: 'roleName', key: 'roleName' },
  { title: t('system.role.roleKey'), dataIndex: 'roleKey', key: 'roleKey' },
  { title: t('common.status'), dataIndex: 'status', key: 'status', width: 80 },
  { title: t('common.createTime'), dataIndex: 'createTime', key: 'createTime', width: 160 },
]

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showTotal: (total: number) => `${t('common.total')} ${total} ${t('common.items')}`,
  onChange: (page: number) => {
    pagination.current = page
  },
})

// 行选择配置
const rowSelection: TableProps['rowSelection'] = {
  selectedRowKeys: selectedRoleIds.value as any,
  onChange: (keys: Key[]) => {
    selectedRoleIds.value = keys as number[]
  },
  getCheckboxProps: (record: any) => ({
    disabled: record.status !== '0', // 停用的角色不可选
  }),
}

// 获取用户角色信息
const getUserRoles = async () => {
  if (!props.userId) return

  loading.value = true
  try {
    const res = await getUserRoleList(props.userId)
    if (res.code === 200) {
      userInfo.value = res.data
      roleList.value = res.data.roles || []
      pagination.total = roleList.value.length

      // 设置已选中的角色
      selectedRoleIds.value = res.data.roleIds || []
    }
  } catch (error) {
    message.error(t('system.user.getUserRoleInfoFailed'))
  } finally {
    loading.value = false
  }
}

// 格式化时间
const formatTime = (time: string | undefined) => {
  if (!time) return ''
  return parseTime(time)
}

// 提交表单
const handleSubmit = async () => {
  if (!props.userId) return

  loading.value = true
  try {
    const data: UserRoleUpdateDTO = {
      userId: props.userId,
      roleIds: selectedRoleIds.value,
    }
    const res = await updateUserRole(data)
    if (res.code === 200) {
      message.success(t('system.user.assignRoleSuccess'))
      emit('success')
    }
  } catch (error) {
    message.error(t('system.user.assignRoleFailed'))
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  emit('update:visible', false)
}

// 重置数据
const resetData = () => {
  userInfo.value = {} as UserInfo
  roleList.value = []
  selectedRoleIds.value = []
  pagination.current = 1
  pagination.total = 0
}

// 监听弹窗显示
watch(
  () => props.visible,
  (val) => {
    if (val) {
      getUserRoles()
    } else {
      resetData()
    }
  }
)
</script>

<style scoped>
.role-section {
  margin-top: 24px;

  h4 {
    margin-bottom: 16px;
    font-weight: 500;
    font-size: 16px;
  }
}

:deep(.ant-descriptions) {
  margin-bottom: 16px;
}

:deep(.ant-table) {
  font-size: 13px;
}
</style>
