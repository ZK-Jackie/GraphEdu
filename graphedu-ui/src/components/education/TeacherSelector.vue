<template>
  <a-modal
    :open="visible"
    title="选择教师"
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
        <a-form-item label="工号">
          <a-input
            v-model:value="searchParams.teacherNo"
            placeholder="请输入工号"
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

      <!-- 教师列表 -->
      <a-table
        :data-source="teacherList"
        :loading="loading"
        :row-selection="rowSelection"
        :pagination="pagination"
        :row-key="(record) => record.teacherId"
        :scroll="{ y: 400 }"
        size="small"
      >
        <a-table-column key="teacherNo" title="工号" data-index="teacherNo" width="120" />
          <a-table-column key="realName" title="姓名" data-index="realName" width="100" />
          <a-table-column key="faculty" title="学院" data-index="faculty" width="150" />
          <a-table-column key="title" title="职称" data-index="title" width="120" />
          <a-table-column key="researchDirection" title="研究方向" data-index="researchDirection" width="200" />
      </a-table>
    </a-space>
  </a-modal>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import type { Key } from 'ant-design-vue/es/_util/type'
import request from '@/utils/request'
import type { ResponseType, PageResponse } from '@/types/api/common'
import type { TeacherListVO } from '@/types/api/education/teacher.ts'

interface Props {
  visible: boolean
  excludedUserId?: number // 排除当前编辑的用户ID（用于编辑时）
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'select', teacher: TeacherListVO): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 搜索参数
const searchParams = ref<{
  realName?: string
  teacherNo?: string
  faculty?: string
  page?: number
  size?: number
}>({
  page: 1,
  size: 10,
})

// 教师列表
const teacherList = ref<TeacherListVO[]>([])
const total = ref(0)
const loading = ref(false)
const selectedTeacherId = ref<number | null>(null)

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
    loadTeachers()
  },
}))

// 行选择配置（单选模式）
const rowSelection = computed(() => ({
  type: 'radio' as const,
  selectedRowKeys: selectedTeacherId.value ? [selectedTeacherId.value] : [] as Key[],
  onChange: (selectedRowKeys: Key[]) => {
    selectedTeacherId.value = (selectedRowKeys[0] as number) || null
  },
}))

// 加载教师列表
const loadTeachers = async () => {
  loading.value = true
  try {
    const res: ResponseType<PageResponse<TeacherListVO>> = await request({
      url: '/system/user/unbound-teachers',
      method: 'get',
      params: searchParams.value,
    })

    if (res.code === 200 && res.data) {
      teacherList.value = res.data.rows || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    console.error('加载教师列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  searchParams.value.page = 1
  loadTeachers()
}

// 重置
const handleReset = () => {
  searchParams.value = {
    realName: undefined,
    teacherNo: undefined,
    faculty: undefined,
    page: 1,
    size: 10,
  }
  selectedTeacherId.value = null
  loadTeachers()
}

// 确认
const handleOk = () => {
  if (selectedTeacherId.value) {
    const teacher = teacherList.value.find((t) => t.teacherId === selectedTeacherId.value)
    if (teacher) {
      emit('select', teacher)
      emit('update:visible', false)
    }
  }
}

// 取消
const handleCancel = () => {
  emit('update:visible', false)
  selectedTeacherId.value = null
}

// 监听visible变化，加载数据
watch(
  () => props.visible,
  (newVisible) => {
    if (newVisible) {
      selectedTeacherId.value = null
      loadTeachers()
    }
  }
)
</script>

<style scoped>
:deep(.ant-table) {
  font-size: 14px;
}
</style>
