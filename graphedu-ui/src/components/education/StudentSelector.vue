<template>
  <a-modal
    :open="visible"
    title="选择学生"
    :width="900"
    :confirm-loading="loading"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <a-space direction="vertical" style="width: 100%">
      <!-- 搜索框 -->
      <a-form layout="inline">
        <a-form-item label="姓名">
          <a-input
            v-model:value="searchParams.realName"
            placeholder="请输入姓名"
            allow-clear
            style="width: 150px"
            @press-enter="handleSearch"
          />
        </a-form-item>
        <a-form-item label="学号">
          <a-input
            v-model:value="searchParams.studentNo"
            placeholder="请输入学号"
            allow-clear
            style="width: 150px"
            @press-enter="handleSearch"
          />
        </a-form-item>
        <a-form-item label="学院">
          <a-input
            v-model:value="searchParams.faculty"
            placeholder="请输入学院"
            allow-clear
            style="width: 150px"
            @press-enter="handleSearch"
          />
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="handleSearch">
              <SearchOutlined />
              搜索
            </a-button>
            <a-button @click="handleReset">
              <ReloadOutlined />
              重置
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>

      <!-- 学生列表 -->
      <a-table
        :data-source="studentList"
        :loading="loading"
        :row-selection="rowSelection"
        :pagination="pagination"
        :row-key="(record) => record.studentId"
        :scroll="{ y: 400 }"
        size="small"
      >
        <a-table-column key="studentNo" title="学号" data-index="studentNo" width="120" />
          <a-table-column key="realName" title="姓名" data-index="realName" width="100" />
          <a-table-column key="faculty" title="学院" data-index="faculty" width="150" />
          <a-table-column key="major" title="专业" data-index="major" width="150" />
          <a-table-column key="grade" title="年级" data-index="grade" width="100" />
          <a-table-column key="className" title="班级" data-index="className" width="120" />
      </a-table>
    </a-space>
  </a-modal>
</template>

<script setup lang="ts">
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import type { Key } from 'ant-design-vue/es/_util/type'
import request from '@/utils/request'
import type { ResponseType, PageResponse } from '@/types/api/common'
import type { StudentListVO } from '@/types/api/education/student.ts'

interface Props {
  visible: boolean
  excludedUserId?: number // 排除当前编辑的用户ID（用于编辑时）
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'select', student: StudentListVO): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 搜索参数
const searchParams = ref<{
  realName?: string
  studentNo?: string
  faculty?: string
  page?: number
  size?: number
}>({
  page: 1,
  size: 10,
})

// 学生列表
const studentList = ref<StudentListVO[]>([])
const total = ref(0)
const loading = ref(false)
const selectedStudentId = ref<number | null>(null)

// 分页配置
const pagination = computed(() => ({
  current: searchParams.value.page || 1,
  pageSize: searchParams.value.size || 10,
  total: total.value,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`,
  onChange: (page: number, pageSize: number) => {
    searchParams.value.page = page
    searchParams.value.size = pageSize
    loadStudents()
  },
}))

// 行选择配置（单选模式）
const rowSelection = computed(() => ({
  type: 'radio' as const,
  selectedRowKeys: selectedStudentId.value ? [selectedStudentId.value] : [] as Key[],
  onChange: (selectedRowKeys: Key[]) => {
    selectedStudentId.value = (selectedRowKeys[0] as number) || null
  },
}))

// 加载学生列表
const loadStudents = async () => {
  loading.value = true
  try {
    const res: ResponseType<PageResponse<StudentListVO>> = await request({
      url: '/system/user/unbound-students',
      method: 'get',
      params: searchParams.value,
    })

    if (res.code === 200 && res.data) {
      studentList.value = res.data.rows || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    console.error('加载学生列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  searchParams.value.page = 1
  loadStudents()
}

// 重置
const handleReset = () => {
  searchParams.value = {
    realName: undefined,
    studentNo: undefined,
    faculty: undefined,
    page: 1,
    size: 10,
  }
  selectedStudentId.value = null
  loadStudents()
}

// 确认
const handleOk = () => {
  if (selectedStudentId.value) {
    const student = studentList.value.find((s) => s.studentId === selectedStudentId.value)
    if (student) {
      emit('select', student)
      emit('update:visible', false)
    }
  }
}

// 取消
const handleCancel = () => {
  emit('update:visible', false)
  selectedStudentId.value = null
}

// 监听visible变化，加载数据
watch(
  () => props.visible,
  (newVisible) => {
    if (newVisible) {
      selectedStudentId.value = null
      loadStudents()
    }
  }
)
</script>

<style scoped>
:deep(.ant-table) {
  font-size: 14px;
}
</style>
