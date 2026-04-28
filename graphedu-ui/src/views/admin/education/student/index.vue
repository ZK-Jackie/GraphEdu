<template>
  <TablePageLayout>
    <!-- 搜索表单 -->
    <template #search>
      <a-card :bordered="false">
        <a-form layout="inline" :model="queryParams">
          <a-form-item label="真实姓名">
            <a-input
              v-model:value="queryParams.realName"
              placeholder="请输入真实姓名"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item label="学号">
            <a-input
              v-model:value="queryParams.studentNo"
              placeholder="请输入学号"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item label="学院">
            <a-input
              v-model:value="queryParams.faculty"
              placeholder="请输入学院"
              allow-clear
              style="width: 150px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item label="专业">
            <a-input
              v-model:value="queryParams.major"
              placeholder="请输入专业"
              allow-clear
              style="width: 150px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item label="年级">
            <a-input
              v-model:value="queryParams.grade"
              placeholder="请输入年级"
              allow-clear
              style="width: 120px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item label="班级">
            <a-input
              v-model:value="queryParams.className"
              placeholder="请输入班级"
              allow-clear
              style="width: 120px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item label="状态">
            <a-select v-model:value="queryParams.status" placeholder="请选择状态" allow-clear style="width: 120px">
              <a-select-option value="0">正常</a-select-option>
              <a-select-option value="1">停用</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item>
            <a-space>
              <a-button type="primary" @click="handleQuery">
                <template #icon><SearchOutlined /></template>
                搜索
              </a-button>
              <a-button @click="resetQuery">
                <template #icon><ReloadOutlined /></template>
                重置
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
          新增
        </a-button>
        <a-button type="default" :disabled="!isSingleSelected" @click="handleEdit">
          <template #icon><EditOutlined /></template>
          修改
        </a-button>
        <a-button danger type="default" :disabled="!hasSelected" @click="handleDelete">
          <template #icon><DeleteOutlined /></template>
          删除
        </a-button>
      </a-space>
    </template>

    <!-- 表格 -->
    <template #table="{ scrollY }">
      <a-table
        :columns="columns"
        :data-source="studentList"
        :loading="loading"
        :row-selection="rowSelection as any"
        :pagination="false"
        row-key="studentId"
        :scroll="{ x: 'max-content', y: scrollY }"
      >
        <template #bodyCell="{ column, record }">
          <!-- 性别列 -->
          <template v-if="column.key === 'gender'">
            <a-tag v-if="record.gender === 1" color="blue">男</a-tag>
            <a-tag v-else-if="record.gender === 2" color="pink">女</a-tag>
            <a-tag v-else color="default">未知</a-tag>
          </template>

          <!-- 状态列 -->
          <template v-else-if="column.key === 'status'">
            <a-switch
              :checked="record.status === '0'"
              checked-children="正常"
              un-checked-children="停用"
              @change="(checked: any) => handleStatusChange(record as StudentListVO, checked)"
            />
          </template>

          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" :loading="formLoading" @click="handleEdit(record as StudentListVO)">
                <template #icon><EditOutlined /></template>
                修改
              </a-button>
              <a-button type="link" size="small" danger @click="handleDelete(record as StudentListVO)">
                <template #icon><DeleteOutlined /></template>
                删除
              </a-button>
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
        :show-total="(total) => `共 ${total} 条`"
        @change="handlePageChange"
      />
    </template>
  </TablePageLayout>

  <!-- 新增/编辑弹窗 -->
  <a-modal
    v-model:open="formVisible"
    :title="formTitle"
    :confirm-loading="formLoading"
    width="800px"
    @ok="handleSubmit"
    @cancel="handleCancel"
  >
    <a-form ref="formRef" :model="form" :rules="rules as any" :label-col="{ span: 6 }">
      <!-- 用户选择器（仅新增时显示） -->
      <a-form-item v-if="!isEdit" label="关联用户" name="studentId">
        <a-select
          v-model:value="form.studentId"
          placeholder="请选择关联用户"
          :loading="availableUsersLoading"
          show-search
          :filter-option="filterUser"
          allow-clear
        >
          <a-select-option v-for="user in availableUsers" :key="user.userId" :value="user.userId">
            {{ user.userName }} - {{ user.nickName }}
          </a-select-option>
        </a-select>
      </a-form-item>
      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="真实姓名" name="realName">
            <a-input v-model:value="form.realName" placeholder="请输入真实姓名" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="学号" name="studentNo">
            <a-input v-model:value="form.studentNo" placeholder="请输入学号" />
          </a-form-item>
        </a-col>
      </a-row>
      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="学院" name="faculty">
            <a-input v-model:value="form.faculty" placeholder="请输入学院" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="专业" name="major">
            <a-input v-model:value="form.major" placeholder="请输入专业" />
          </a-form-item>
        </a-col>
      </a-row>
      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="年级" name="grade">
            <a-input v-model:value="form.grade" placeholder="请输入年级" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="班级" name="className">
            <a-input v-model:value="form.className" placeholder="请输入班级" />
          </a-form-item>
        </a-col>
      </a-row>
      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="性别" name="gender">
            <a-select v-model:value="form.gender" placeholder="请选择性别" allow-clear>
              <a-select-option :value="0">未知</a-select-option>
              <a-select-option :value="1">男</a-select-option>
              <a-select-option :value="2">女</a-select-option>
              <a-select-option :value="9">其他</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="年龄" name="age">
            <a-input-number v-model:value="form.age" placeholder="请输入年龄" :min="1" :max="120" style="width: 100%" />
          </a-form-item>
        </a-col>
      </a-row>
      <a-form-item label="自我介绍" name="description">
        <a-textarea v-model:value="form.description" placeholder="请输入自我介绍" :rows="3" />
      </a-form-item>
      <a-form-item v-if="isEdit" label="状态" name="status">
        <a-radio-group v-model:value="form.status">
          <a-radio-value value="0">正常</a-radio-value>
          <a-radio-value value="1">停用</a-radio-value>
        </a-radio-group>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import type { FormInstance, TableProps } from 'ant-design-vue'
import { SearchOutlined, ReloadOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import {
  getStudentList,
  addStudent,
  updateStudent,
  deleteStudent,
  changeStudentStatus,
  getStudentDetail,
} from '@/api/education/student.ts'
import { getAvailableUsersForStudent } from '@/api/system/user.ts'
import type { UserListVO } from '@/types/api/system/user.ts'
import type {
  StudentCreateDTO,
  StudentListVO,
  StudentQueryDTO,
  StudentUpdateDTO,
} from '@/types/api/education/student.ts'
import { parseTime } from '@/utils/common.ts'
import TablePageLayout from '@/layout/TablePageLayout.vue'
import usePaginationQuery from '@/composables/usePaginationQuery.ts'

// 查询参数的默认值
const defaultQueryParams: StudentQueryDTO = {
  page: 1,
  size: 10,
  realName: undefined,
  studentNo: undefined,
  faculty: undefined,
  major: undefined,
  grade: undefined,
  className: undefined,
  status: undefined,
}

// 临时存储查询参数（在 getList 中使用）
let queryParams: StudentQueryDTO = { ...defaultQueryParams }

// 表格数据
const loading = ref(false)
const studentList = ref<StudentListVO[]>([])
const total = ref(0)

// 可用用户列表（用于新增学生时选择关联用户）
const availableUsers = ref<UserListVO[]>([])
const availableUsersLoading = ref(false)

// 表格列定义
const columns = [
  { title: 'ID', dataIndex: 'studentId', key: 'studentId', width: 80, fixed: 'left' as const },
  { title: '真实姓名', dataIndex: 'realName', key: 'realName', width: 120 },
  { title: '学号', dataIndex: 'studentNo', key: 'studentNo', width: 120 },
  { title: '学院', dataIndex: 'faculty', key: 'faculty', width: 150 },
  { title: '专业', dataIndex: 'major', key: 'major', width: 150 },
  { title: '年级', dataIndex: 'grade', key: 'grade', width: 100 },
  { title: '班级', dataIndex: 'className', key: 'className', width: 120 },
  { title: '性别', dataIndex: 'gender', key: 'gender', width: 80 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: '操作', key: 'action', fixed: 'right' as const, width: 180 },
]

// 行选择
const selectedRowKeys = ref<number[]>([])
const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: number[]) => {
    selectedRowKeys.value = keys
  },
}))

const isSingleSelected = computed(() => selectedRowKeys.value.length === 1)
const hasSelected = computed(() => selectedRowKeys.value.length > 0)

// 表单相关
const formVisible = ref(false)
const formLoading = ref(false)
const formTitle = computed(() => (isEdit.value ? '修改学生' : '新增学生'))
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const form = reactive<Partial<StudentCreateDTO & StudentUpdateDTO>>({
  studentId: undefined,
  realName: '',
  studentNo: '',
  faculty: '',
  major: '',
  grade: '',
  className: '',
  gender: undefined,
  age: undefined,
  description: '',
  status: '0',
})

const rules = {
  realName: [{ required: true, message: '请输入真实姓名' }],
  studentId: [{ required: true, message: '请选择关联用户' }],
}

// 查询列表
const getList = async () => {
  loading.value = true
  try {
    const res = await getStudentList(queryParams)
    if (res.data) {
      studentList.value = res.data.rows || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    console.error('获取学生列表失败:', error)
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
} = usePaginationQuery<StudentQueryDTO>(defaultQueryParams, getList, {
  syncSearchParams: true,
  searchParamKeys: ['realName', 'studentNo', 'faculty', 'major', 'grade', 'className', 'status'],
  debounceUrlUpdate: true,
  debounceDelay: 300,
})

// 使用 hook 返回的 queryParams
queryParams = syncedQueryParams

// 搜索
const handleQuery = () => {
  queryParams.page = 1
  getList()
}

// 重置
const resetQuery = () => {
  resetAll()
  fetch()
}

// 分页变化
const handlePageChange = () => {
  getList()
}

// 获取可用用户列表
const fetchAvailableUsers = async () => {
  availableUsersLoading.value = true
  try {
    const res = await getAvailableUsersForStudent()
    if (res.data) {
      availableUsers.value = res.data
    }
  } catch (error) {
    console.error('获取可用用户列表失败:', error)
  } finally {
    availableUsersLoading.value = false
  }
}

// 用户选择器过滤函数
const filterUser = (input: string, option: any) => {
  return option.label.toLowerCase().includes(input.toLowerCase())
}

// 新增
const handleAdd = async () => {
  isEdit.value = false
  Object.assign(form, {
    studentId: undefined,
    realName: '',
    studentNo: '',
    faculty: '',
    major: '',
    grade: '',
    className: '',
    gender: undefined,
    age: undefined,
    description: '',
  })
  // 加载可用用户列表
  await fetchAvailableUsers()
  formVisible.value = true
}

// 编辑
const handleEdit = async (record?: any) => {
  const target = record || studentList.value.find((item) => item.studentId === selectedRowKeys.value[0])
  if (!target) return

  isEdit.value = true
  formLoading.value = true

  try {
    // 调用详情接口获取完整数据
    const res = await getStudentDetail(target.studentId)
    if (res.data) {
      const detail = res.data
      Object.assign(form, {
        studentId: detail.studentId,
        realName: detail.realName,
        studentNo: detail.studentNo,
        faculty: detail.faculty,
        major: detail.major,
        grade: detail.grade,
        className: detail.className,
        gender: detail.gender?.toString() as any,
        age: detail.age,
        description: detail.description || '',
        status: detail.status,
      })
    }
    formVisible.value = true
  } catch (error) {
    console.error('获取学生详情失败:', error)
    message.error('获取学生详情失败')
  } finally {
    formLoading.value = false
  }
}

// 删除
const handleDelete = (record?: any) => {
  const ids = record ? [record.studentId] : selectedRowKeys.value
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除选中的 ${ids.length} 条数据吗？`,
    onOk: async () => {
      try {
        await deleteStudent(ids.join(','))
        message.success('删除成功')
        selectedRowKeys.value = []
        getList()
      } catch (error) {
        console.error('删除失败:', error)
      }
    },
  })
}

// 状态切换
const handleStatusChange = async (record: StudentListVO, checked: boolean) => {
  try {
    await changeStudentStatus({ studentId: record.studentId, status: checked ? '0' : '1' })
    message.success('状态修改成功')
    getList()
  } catch (error) {
    console.error('状态修改失败:', error)
  }
}

// 表单提交
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    formLoading.value = true

    if (isEdit.value) {
      await updateStudent(form as StudentUpdateDTO)
      message.success('修改成功')
    } else {
      await addStudent(form as StudentCreateDTO)
      message.success('新增成功')
    }

    formVisible.value = false
    getList()
  } catch (error) {
    console.error('表单提交失败:', error)
  } finally {
    formLoading.value = false
  }
}

// 表单取消
const handleCancel = () => {
  formVisible.value = false
  formRef.value?.resetFields()
}

// 格式化时间
const formatTime = (time?: string) => {
  if (!time) return '-'
  return parseTime(time)
}

onMounted(() => {
  getList()
})
</script>
