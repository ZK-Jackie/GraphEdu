<template>
  <a-drawer
    v-model:open="drawerOpen"
    :title="t('system.dept.deptUsers')"
    :width="800"
    placement="right"
    @close="handleClose"
  >
    <template #extra>
      <a-tag color="blue">{{ deptName }}</a-tag>
    </template>

    <!-- 用户列表 -->
    <a-table :columns="columns" :data-source="userList" :loading="loading" :pagination="false" row-key="userId">
      <template #bodyCell="{ column, record }">
        <!-- 状态列 -->
        <template v-if="column.key === 'status'">
          <DictTag :options="sys_data_status" :value="record.status" />
        </template>
        <!-- 用户类型列 -->
        <template v-else-if="column.key === 'userType'">
          <DictTag :options="sys_user_type" :value="record.userType" />
        </template>
        <!-- 操作列 -->
        <template v-else-if="column.key === 'action'">
          <a-popconfirm
            :title="t('system.dept.removeUserConfirm')"
            :ok-text="t('common.confirm')"
            :cancel-text="t('common.cancel')"
            @confirm="handleRemoveUser(record as UserListVO)"
          >
            <a-button type="link" size="small" danger>{{ t('system.dept.removeUser') }}</a-button>
          </a-popconfirm>
        </template>
      </template>
    </a-table>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import type { TableProps } from 'ant-design-vue'
import { getDeptUsers, removeUserFromDept } from '@/api/system/dept.ts'
import type { UserListVO } from '@/types/api/system/user.ts'
import { useDict } from '@/utils/dict.ts'
import DictTag from '../../../../../components/dict/DictTag.vue'

const { t } = useI18n()

interface Props {
  visible: boolean
  deptId?: number
  deptName?: string
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 获取字典数据
const { sys_data_status, sys_user_type } = useDict('sys_data_status', 'sys_user_type')

// 用户表格列定义
const columns: TableProps['columns'] = [
  { title: t('system.dept.userId'), dataIndex: 'userId', key: 'userId', width: 80 },
  { title: t('common.userName'), dataIndex: 'userName', key: 'userName', width: 120 },
  { title: t('system.user.nickName'), dataIndex: 'nickName', key: 'nickName', width: 120 },
  { title: t('system.user.userType'), dataIndex: 'userType', key: 'userType', width: 100 },
  { title: t('common.status'), dataIndex: 'status', key: 'status', width: 80 },
  { title: t('common.operation'), key: 'action', fixed: 'right', width: 100 },
]

// 数据状态
const loading = ref(false)
const userList = ref<UserListVO[]>([])
const drawerOpen = ref(false)

// 监听 visible 变化
watch(
  () => props.visible,
  (val) => {
    drawerOpen.value = val
    if (val && props.deptId) {
      getUserList()
    }
  },
  { immediate: true }
)

// 监听 drawerOpen 变化，同步给父组件
watch(drawerOpen, (val) => {
  if (!val) {
    emit('update:visible', false)
  }
})

// 获取用户列表
const getUserList = async () => {
  loading.value = true
  try {
    const res = await getDeptUsers(props.deptId!)
    if (res.code === 200) {
      userList.value = res.data || []
    }
  } catch (_e) {
    message.error(t('common.getUserListFailed'))
  } finally {
    loading.value = false
  }
}

// 移除用户
const handleRemoveUser = async (record: UserListVO) => {
  try {
    const res = await removeUserFromDept(props.deptId!, record.userId)
    if (res.code === 200) {
      message.success(t('system.dept.removeSuccess'))
      emit('success')
      await getUserList()
    }
  } catch (_e) {
    message.error(t('system.dept.removeFailed'))
  }
}

// 关闭抽屉
const handleClose = () => {
  emit('update:visible', false)
  userList.value = []
}
</script>
