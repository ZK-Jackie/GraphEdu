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
          <a-form-item label="工号">
            <a-input
              v-model:value="queryParams.teacherNo"
              placeholder="请输入工号"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item label="所属学院">
            <a-input
              v-model:value="queryParams.faculty"
              placeholder="请输入学院"
              allow-clear
              style="width: 150px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item label="职称">
            <a-input
              v-model:value="queryParams.title"
              placeholder="请输入职称"
              allow-clear
              style="width: 150px"
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
        <a-button type="default" :disabled="!isSingleSelected" @click="handleEdit()">
          <template #icon><EditOutlined /></template>
          修改
        </a-button>
        <a-button danger type="default" :disabled="!hasSelected" @click="handleDelete()">
          <template #icon><DeleteOutlined /></template>
          删除
        </a-button>
      </a-space>
    </template>

    <!-- 表格 -->
    <template #table="{ scrollY }">
      <a-table
        :columns="columns"
        :data-source="teacherList"
        :loading="loading"
        :row-selection="rowSelection"
        :pagination="false"
        row-key="teacherId"
        :scroll="{ x: 'max-content', y: scrollY }"
      >
        <template #bodyCell="{ column, record }">
          <!-- 状态列 -->
          <template v-if="column.key === 'status'">
            <a-switch
              :checked="record.status === '0'"
              checked-children="正常"
              un-checked-children="停用"
              @change="(checked: any) => handleStatusChange(record as TeacherListVO, checked)"
            />
          </template>

          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" :loading="formLoading" @click="handleEdit(record as TeacherListVO)">
                <template #icon><EditOutlined /></template>
                修改
              </a-button>
              <a-button type="link" size="small" danger @click="handleDelete(record as TeacherListVO)">
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
      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="真实姓名" name="realName">
            <a-input v-model:value="form.realName" placeholder="请输入真实姓名" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="工号" name="teacherNo">
            <a-input v-model:value="form.teacherNo" placeholder="请输入工号" />
          </a-form-item>
        </a-col>
      </a-row>
      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="所属学院" name="faculty">
            <a-input v-model:value="form.faculty" placeholder="请输入学院" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="职称" name="title">
            <a-select v-model:value="form.title" placeholder="请选择职称" allow-clear>
              <a-select-option value="教授">教授</a-select-option>
              <a-select-option value="副教授">副教授</a-select-option>
              <a-select-option value="讲师">讲师</a-select-option>
              <a-select-option value="助教">助教</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>
      <a-form-item label="研究方向" name="researchDirection">
        <a-textarea v-model:value="form.researchDirection" placeholder="请输入研究方向" :rows="2" />
      </a-form-item>
      <a-form-item label="个人简介" name="description">
        <a-textarea v-model:value="form.description" placeholder="请输入个人简介" :rows="3" />
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
import type { FormInstance } from 'ant-design-vue'
import { SearchOutlined, ReloadOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import {
  getTeacherList,
  addTeacher,
  updateTeacher,
  deleteTeacher,
  changeTeacherStatus,
  getTeacherDetail,
} from '@/api/education/teacher.ts'
import type { Key } from 'ant-design-vue/es/_util/type'
import type {
  TeacherCreateDTO,
  TeacherListVO,
  TeacherQueryDTO,
  TeacherUpdateDTO,
} from '@/types/api/education/teacher.ts'
import { parseTime } from '@/utils/common.ts'
import TablePageLayout from '@/layout/TablePageLayout.vue'
import usePaginationQuery from '@/composables/usePaginationQuery.ts'

// 查询参数的默认值
const defaultQueryParams: TeacherQueryDTO = {
  page: 1,
  size: 10,
  realName: undefined,
  teacherNo: undefined,
  faculty: undefined,
  title: undefined,
  status: undefined,
}

// 临时存储查询参数（在 getList 中使用）
let queryParams: TeacherQueryDTO = { ...defaultQueryParams }

// 表格数据
const loading = ref(false)
const teacherList = ref<TeacherListVO[]>([])
const total = ref(0)

// 表格列定义
const columns = [
  { title: 'ID', dataIndex: 'teacherId', key: 'teacherId', width: 80, fixed: 'left' as const },
  { title: '真实姓名', dataIndex: 'realName', key: 'realName', width: 120 },
  { title: '工号', dataIndex: 'teacherNo', key: 'teacherNo', width: 120 },
  { title: '所属学院', dataIndex: 'faculty', key: 'faculty', width: 150 },
  { title: '职称', dataIndex: 'title', key: 'title', width: 100 },
  { title: '最大带教数', dataIndex: 'maxStudentCount', key: 'maxStudentCount', width: 120 },
  { title: '当前学生数', dataIndex: 'currentStudentCount', key: 'currentStudentCount', width: 120 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: '操作', key: 'action', fixed: 'right' as const, width: 180 },
]

// 行选择
const selectedRowKeys = ref<Key[]>([])
const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: Key[]) => {
    selectedRowKeys.value = keys
  },
}))

const isSingleSelected = computed(() => selectedRowKeys.value.length === 1)
const hasSelected = computed(() => selectedRowKeys.value.length > 0)

// 表单相关
const formVisible = ref(false)
const formLoading = ref(false)
const formTitle = computed(() => (isEdit.value ? '修改教师' : '新增教师'))
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const form = reactive<Partial<TeacherCreateDTO & TeacherUpdateDTO>>({
  teacherId: undefined,
  realName: '',
  teacherNo: '',
  faculty: '',
  title: undefined,
  researchDirection: '',
  description: '',
  status: '0',
})

const rules = {
  realName: [{ required: true, message: '请输入真实姓名' }],
  teacherId: [{ required: true, message: '请输入教师ID' }],
}

// 查询列表
const getList = async () => {
  loading.value = true
  try {
    const res = await getTeacherList(queryParams)
    if (res.data) {
      teacherList.value = res.data.rows || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    console.error('获取教师列表失败:', error)
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
} = usePaginationQuery<TeacherQueryDTO>(defaultQueryParams, getList, {
  syncSearchParams: true,
  searchParamKeys: ['realName', 'teacherNo', 'faculty', 'title', 'status'],
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

// 新增
const handleAdd = () => {
  isEdit.value = false
  Object.assign(form, {
    teacherId: undefined,
    realName: '',
    teacherNo: '',
    faculty: '',
    title: undefined,
    researchDirection: '',
    description: '',
  })
  formVisible.value = true
}

// 编辑
const handleEdit = async (record?: TeacherListVO) => {
  const target = record || teacherList.value.find((item) => item.teacherId === selectedRowKeys.value[0])
  if (!target) return

  isEdit.value = true

  isEdit.value = true
  formLoading.value = true

  try {
    // 调用详情接口获取完整数据
    const res = await getTeacherDetail(target.teacherId)
    if (res.data) {
      const detail = res.data
      Object.assign(form, {
        teacherId: detail.teacherId,
        realName: detail.realName,
        teacherNo: detail.teacherNo,
        faculty: detail.faculty,
        title: detail.title || undefined,
        researchDirection: detail.researchDirection || '',
        description: detail.description || '',
        status: detail.status,
      })
    }
    formVisible.value = true
  } catch (error) {
    console.error('获取教师详情失败:', error)
    message.error('获取教师详情失败')
  } finally {
    formLoading.value = false
  }
}

// 删除
const handleDelete = (record?: TeacherListVO) => {
  const ids = record ? [record.teacherId] : selectedRowKeys.value
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除选中的 ${ids.length} 条数据吗？`,
    onOk: async () => {
      try {
        await deleteTeacher(ids.join(','))
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
const handleStatusChange = async (record: TeacherListVO, checked: boolean) => {
  try {
    await changeTeacherStatus({ teacherId: record.teacherId, status: checked ? '0' : '1' })
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
      await updateTeacher(form as TeacherUpdateDTO)
      message.success('修改成功')
    } else {
      await addTeacher(form as TeacherCreateDTO)
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
