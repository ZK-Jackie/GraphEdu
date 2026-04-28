<template>
  <TablePageLayout scroll-behavior="auto">
    <!-- 搜索表单 -->
    <template #search>
      <a-card :bordered="false" class="search-card">
        <a-form layout="inline" :model="queryParams">
          <a-form-item :label="t('system.dept.deptName')">
            <a-input
              v-model:value="queryParams.deptName"
              :placeholder="t('system.dept.deptNamePlaceholder')"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item :label="t('common.status')">
            <DictSelect
              v-model:model-value="queryParams.status"
              dict-type="sys_data_status"
              :placeholder="t('system.dept.statusPlaceholder')"
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
        <a-button type="default" @click="toggleExpandAll">
          <template #icon><AlignCenterOutlined /></template>
          {{ t('common.expandCollapse') }}
        </a-button>
      </a-space>
    </template>

    <!-- 部门树表格 -->
    <template #table="{ scrollY }">
      <a-table
        :columns="columns"
        :data-source="deptList"
        :loading="loading"
        :pagination="false"
        row-key="deptId"
        :expanded-row-keys="expandedRowKeys"
        :scroll="{ x: 'max-content', y: scrollY }"
        @expand="toggleExpandRow"
      >
        <template #bodyCell="{ column, record }">
          <!-- 状态列 -->
          <template v-if="column.key === 'status'">
            <DictTag :options="sys_data_status" :value="record.status" />
          </template>
          <!-- 时间列 -->
          <template v-else-if="column.key === 'createTime'">
            {{ formatTime(record.createTime) }}
          </template>
          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-tooltip :title="t('common.edit')">
                <a-button type="link" size="small" @click="handleUpdate(record as DeptTreeVO)">
                  <template #icon><EditOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip :title="t('system.dept.addChild')">
                <a-button type="link" size="small" @click="handleAddChild(record as DeptTreeVO)">
                  <template #icon><PlusOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip :title="t('system.dept.viewUsers')">
                <a-button type="link" size="small" @click="handleViewUsers(record as DeptTreeVO)">
                  <template #icon><UserOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip v-if="record.parentId !== 0" :title="t('common.delete')">
                <a-button type="link" size="small" danger @click="handleDelete(record as DeptTreeVO)">
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </a-tooltip>
            </a-space>
          </template>
        </template>
      </a-table>
    </template>
  </TablePageLayout>

  <!-- 部门表单组件 -->
  <DeptForm
    v-model:visible="formVisible"
    :dept-id="currentDeptId"
    :parent-id="currentParentId"
    @success="handleFormSuccess"
  />

  <!-- 部门用户抽屉组件 -->
  <DeptUsersDrawer
    v-model:visible="usersDrawerVisible"
    :dept-id="currentDeptId"
    :dept-name="currentDeptName"
    @success="handleUsersSuccess"
  />
</template>

<script setup lang="ts">
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  SearchOutlined,
  ReloadOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  AlignCenterOutlined,
  UserOutlined,
} from '@ant-design/icons-vue'
import { getDeptList, getDeptListLazy, deleteDept } from '@/api/system/dept.ts'
import type { DeptQueryDTO, DeptTreeVO } from '@/types/api/system/dept.ts'
import { useDict } from '@/utils/dict.ts'
import { parseTime } from '@/utils/common.ts'
import DictTag from '../../../../components/dict/DictTag.vue'
import DictSelect from '../../../../components/dict/DictSelect.vue'
import TablePageLayout from '@/layout/TablePageLayout.vue'
import DeptForm from './components/DeptForm.vue'
import DeptUsersDrawer from './components/DeptUsersDrawer.vue'

const { t } = useI18n()

// 获取字典数据
const { sys_data_status } = useDict('sys_data_status')

// 部门表格列定义
const columns = [
  { title: t('system.dept.deptName'), dataIndex: 'deptName', key: 'deptName', width: 260 },
  { title: t('common.sortDisplay'), dataIndex: 'sortOrder', key: 'sortOrder', width: 120 },
  { title: t('common.status'), dataIndex: 'status', key: 'status', width: 100 },
  { title: t('common.createTime'), dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: t('common.operation'), key: 'action', fixed: 'right' as const, width: 240 },
]

// 数据状态
const loading = ref(false)
const deptList = ref<DeptTreeVO[]>([])
const isExpandAll = ref(false)
const expandedRowKeys = ref<number[]>([])
// 跟踪已加载的节点ID（该节点的 children 已加载）
const loadedKeys = ref<Set<number>>(new Set())

// 查询参数
const queryParams = reactive<DeptQueryDTO>({
  deptName: undefined,
  status: undefined,
})

// 弹窗状态
const formVisible = ref(false)
const usersDrawerVisible = ref(false)
const currentDeptId = ref<number>()
const currentParentId = ref<number>()
const currentDeptName = ref('')

// 检查是否有查询条件
const hasQueryConditions = () => {
  return !!(queryParams.deptName || queryParams.status !== undefined)
}

// 获取部门列表
const getList = async () => {
  loading.value = true
  loadedKeys.value.clear()
  expandedRowKeys.value = []

  try {
    if (hasQueryConditions()) {
      // 有查询条件时，使用 list 接口一次性加载全部数据
      const res = await getDeptList(queryParams)
      if (res.code === 200) {
        deptList.value = buildTree(res.data || [])
      }
    } else {
      // 无查询条件时，使用异步加载模式，只加载顶层
      const res = await getDeptListLazy(0)
      if (res.code === 200) {
        deptList.value = res.data || []
      }
    }
  } catch (_e) {
    message.error(t('system.dept.getDeptListFailed'))
  } finally {
    loading.value = false
  }
}

// 构建树形结构（搜索模式下使用）
const buildTree = (list: DeptTreeVO[]): DeptTreeVO[] => {
  const map = new Map<number, DeptTreeVO>()
  const tree: DeptTreeVO[] = []

  // 先创建映射（不预设 children，避免叶子节点显示展开箭头）
  list.forEach((item) => {
    map.set(item.deptId, { ...item })
  })

  // 构建树
  list.forEach((item) => {
    const node = map.get(item.deptId)!
    if (item.parentId === 0) {
      tree.push(node)
    } else {
      const parent = map.get(item.parentId)
      if (parent) {
        parent.children ??= []
        parent.children.push(node)
      }
    }
  })

  return tree
}

// 格式化时间
const formatTime = (time: string | undefined) => {
  if (!time) return ''
  return parseTime(time)
}

// 搜索
const handleQuery = () => {
  getList()
}

// 重置查询
const resetQuery = () => {
  queryParams.deptName = undefined
  queryParams.status = undefined
  getList()
}

// 递归加载并展开所有节点的辅助函数
const expandAllNodes = async (nodes: DeptTreeVO[]): Promise<void> => {
  for (const node of nodes) {
    // 检查节点是否有子节点但还没加载 children
    if (node.hasChildren && !loadedKeys.value.has(node.deptId)) {
      try {
        const res = await getDeptListLazy(node.deptId)
        if (res.code === 200) {
          const children = res.data || []
          if (children.length > 0) {
            node.children = children
          } else {
            delete node.children
          }
          // 标记该节点的 children 已加载（无论是否为空）
          loadedKeys.value.add(node.deptId)
        }
      } catch (_e) {
        // 忽略错误，继续处理其他节点
      }
    }

    // 添加到展开列表
    if (!expandedRowKeys.value.includes(node.deptId)) {
      expandedRowKeys.value.push(node.deptId)
    }

    // 递归处理子节点
    if (node.children && node.children.length > 0) {
      await expandAllNodes(node.children)
    }
  }
}

// 展开/折叠所有
const toggleExpandAll = async () => {
  isExpandAll.value = !isExpandAll.value

  if (isExpandAll.value) {
    // 展开所有节点：递归加载并展开
    await expandAllNodes(deptList.value)
  } else {
    // 折叠所有节点
    expandedRowKeys.value = []
  }
}

// 展开/折叠指定行（支持异步加载子节点）
const toggleExpandRow = async (expanded: boolean, record: DeptTreeVO) => {
  if (expanded) {
    // 展开时，检查是否需要加载子节点
    if (!loadedKeys.value.has(record.deptId) && record.hasChildren) {
      try {
        const res = await getDeptListLazy(record.deptId)
        if (res.code === 200) {
          const children = res.data || []
          // 查找并更新父节点的 children
          const updateNode = (list: DeptTreeVO[]): boolean => {
            for (const node of list) {
              if (node.deptId === record.deptId) {
                if (children.length > 0) {
                  node.children = children
                } else {
                  delete node.children
                }
                return true
              }
              if (node.children) {
                if (updateNode(node.children)) {
                  return true
                }
              }
            }
            return false
          }
          updateNode(deptList.value)
          // 标记该节点的 children 已加载
          loadedKeys.value.add(record.deptId)
        }
      } catch (_e) {
        message.error(t('system.dept.getDeptListFailed'))
      }
    }
    // 添加到展开列表
    expandedRowKeys.value = [...expandedRowKeys.value, record.deptId]
  } else {
    // 折叠时，递归收集所有子孙节点ID
    const collectChildIds = (node: DeptTreeVO, ids: number[] = []) => {
      if (node.children) {
        for (const child of node.children) {
          ids.push(child.deptId)
          collectChildIds(child, ids)
        }
      }
      return ids
    }
    const childIds = collectChildIds(record)
    // 从展开列表中移除当前节点及所有子孙节点
    expandedRowKeys.value = expandedRowKeys.value.filter((id) => id !== record.deptId && !childIds.includes(id))
  }
}

// 新增部门
const handleAdd = () => {
  currentDeptId.value = undefined
  currentParentId.value = 0
  formVisible.value = true
}

// 新增子部门
const handleAddChild = (record: DeptTreeVO) => {
  currentDeptId.value = undefined
  currentParentId.value = record.deptId
  formVisible.value = true
}

// 修改部门
const handleUpdate = (record: DeptTreeVO) => {
  currentDeptId.value = record.deptId
  currentParentId.value = undefined
  formVisible.value = true
}

// 删除部门
const handleDelete = (record: DeptTreeVO) => {
  Modal.confirm({
    title: t('common.systemTip'),
    content: t('system.dept.deleteDeptConfirm', { deptName: record.deptName }),
    onOk: async () => {
      try {
        const res = await deleteDept(String(record.deptId))
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

// 查看部门用户
const handleViewUsers = (record: DeptTreeVO) => {
  currentDeptId.value = record.deptId
  currentDeptName.value = record.deptName
  usersDrawerVisible.value = true
}

// 表单提交成功
const handleFormSuccess = () => {
  formVisible.value = false
  getList()
}

// 用户操作成功
const handleUsersSuccess = () => {
  // 不需要关闭抽屉，只需要刷新用户列表
}

// 初始化
onMounted(() => {
  getList()
})
</script>
