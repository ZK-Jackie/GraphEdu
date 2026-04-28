<template>
  <TablePageLayout scroll-behavior="auto">
    <!-- 搜索表单 -->
    <template #search>
      <a-card :bordered="false" class="search-card">
        <a-form layout="inline" :model="queryParams">
          <a-form-item :label="t('system.function.functionName')">
            <a-input
              v-model:value="queryParams.functionName"
              :placeholder="t('system.function.functionNamePlaceholder')"
              allow-clear
              style="width: 200px"
              @press-enter="handleQuery"
            />
          </a-form-item>
          <a-form-item :label="t('system.function.functionType')">
            <DictSelect
              v-model:model-value="queryParams.functionType"
              dict-type="sys_function_type"
              :placeholder="t('system.function.functionTypePlaceholder')"
              allow-clear
              style="width: 120px"
            />
          </a-form-item>
          <a-form-item :label="t('common.status')">
            <DictSelect
              v-model:model-value="queryParams.status"
              dict-type="sys_data_status"
              :placeholder="t('system.function.statusPlaceholder')"
              allow-clear
              style="width: 150px"
            />
          </a-form-item>
          <a-form-item :label="t('system.function.visible')">
            <DictSelect
              v-model:model-value="queryParams.visible"
              dict-type="sys_data_option"
              :placeholder="t('system.function.visiblePlaceholder')"
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
    <template #actions>
      <div class="actions-container">
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

        <!-- 右侧筛选：应用场景 -->
        <div class="actions-filter">
          <DictSelect
            v-model:model-value="queryParams.scene"
            dict-type="sys_function_scene"
            :placeholder="t('system.function.scene')"
            :allow-clear="false"
            style="width: 150px"
            @change="handleQuery"
          />
        </div>
      </div>
    </template>

    <template #table="{ scrollY }">
      <!-- 功能表格（树形） -->
      <a-table
        :columns="columns"
        :data-source="functionList"
        :loading="loading"
        :pagination="false"
        row-key="functionId"
        :expanded-row-keys="expendedRowKeys"
        :scroll="{ x: 'max-content', y: scrollY }"
        @expand="toggleExpandRow"
      >
        <template #bodyCell="{ column, record }">
          <!-- 功能名称 -->
          <template v-if="column.key === 'functionName'">
            <a-space>
              <SvgIcon v-if="record.icon" :icon="record.icon" />
              <span>{{ record.functionName }}</span>
              <!-- 异步加载子节点时显示 loading -->
              <a-spin v-if="loadingKeys.has(record.functionId)" size="small" />
            </a-space>
          </template>

          <!-- 功能类型 -->
          <template v-else-if="column.key === 'functionType'">
            <DictTag :options="sys_function_type" :value="record.functionType" />
          </template>

          <!-- 状态 -->
          <template v-else-if="column.key === 'status'">
            <DictTag :options="sys_data_status" :value="record.status" />
          </template>

          <!-- 是否可见 -->
          <template v-else-if="column.key === 'visible'">
            <DictTag :options="sys_data_option" :value="record.visible" />
          </template>

          <!-- 路由缓存 -->
          <template v-else-if="column.key === 'routeCache'">
            <DictTag :options="sys_data_option" :value="record.routeCache" />
          </template>

          <!-- 是否外链 -->
          <template v-else-if="column.key === 'routeExternal'">
            <DictTag :options="sys_data_option" :value="record.routeExternal" />
          </template>

          <!-- 应用场景 -->
          <template v-else-if="column.key === 'scene'">
            <DictTag :options="sys_function_scene" :value="record.scene" />
          </template>

          <!-- 创建时间 -->
          <template v-else-if="column.key === 'createTime'">
            {{ formatTime(record.createTime) }}
          </template>

          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-tooltip :title="t('common.edit')">
                <a-button type="link" size="small" @click="handleUpdate(record as FunctionTreeVO)">
                  <template #icon><EditOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip :title="t('system.function.addChildFunction')">
                <a-button type="link" size="small" @click="handleAddChild(record as FunctionTreeVO)">
                  <template #icon><PlusOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip :title="t('common.delete')">
                <a-button type="link" size="small" danger @click="handleDelete(record as FunctionTreeVO)">
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </a-tooltip>
            </a-space>
          </template>
        </template>
      </a-table>
    </template>
  </TablePageLayout>

  <!-- 功能表单弹窗 -->
  <FunctionForm
    v-model:visible="formVisible"
    :function-id="currentFunctionId"
    :parent-id="currentParentId"
    :parent-scene="currentParentScene"
    @success="handleFormSuccess"
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
} from '@ant-design/icons-vue'
import { useDict } from '@/utils/dict.ts'
import { getFunctionList, getFunctionListLazy, deleteFunction } from '@/api/system/function.ts'
import type { FunctionQueryDTO, FunctionTreeVO } from '@/types/api/system/function.ts'
import FunctionForm from './components/FunctionForm.vue'
import { parseTime } from '@/utils/common.ts'
import DictTag from '../../../../components/dict/DictTag.vue'
import DictSelect from '../../../../components/dict/DictSelect.vue'
import SvgIcon from '@/components/SvgIcon/index.vue'
import TablePageLayout from '@/layout/TablePageLayout.vue'

const { t } = useI18n()

// 获取字典数据
const { sys_data_option, sys_data_status, sys_function_type, sys_function_scene } = useDict(
  'sys_data_option',
  'sys_data_status',
  'sys_function_type',
  'sys_function_scene'
)

// 表格列定义
const columns = [
  {
    title: t('system.function.functionName'),
    dataIndex: 'functionName',
    key: 'functionName',
    width: 200,
    fixed: 'left' as const,
  },
  { title: t('system.function.functionType'), dataIndex: 'functionType', key: 'functionType', width: 100 },
  { title: t('system.function.permission'), dataIndex: 'functionKey', key: 'functionKey', width: 150, ellipsis: true },
  { title: t('system.function.routePath'), dataIndex: 'routePath', key: 'routePath', width: 150, ellipsis: true },
  { title: t('system.function.component'), dataIndex: 'component', key: 'component', width: 150, ellipsis: true },
  {
    title: t('system.function.layoutComponent'),
    dataIndex: 'layoutComponent',
    key: 'layoutComponent',
    width: 150,
    ellipsis: true,
  },
  { title: t('system.function.routeCache'), dataIndex: 'routeCache', key: 'routeCache', width: 90 },
  { title: t('system.function.routeExternal'), dataIndex: 'routeExternal', key: 'routeExternal', width: 90 },
  { title: t('system.function.scene'), dataIndex: 'scene', key: 'scene', width: 100 },
  { title: t('common.status'), dataIndex: 'status', key: 'status', width: 80 },
  { title: t('system.function.visible'), dataIndex: 'visible', key: 'visible', width: 80 },
  { title: t('common.createTime'), dataIndex: 'createTime', key: 'createTime', width: 160 },
  { title: t('common.operation'), key: 'action', fixed: 'right' as const, width: 180 },
]

// 数据状态
const loading = ref(false)
const functionList = ref<FunctionTreeVO[]>([])
const isExpandAll = ref(false)
const expendedRowKeys = ref<number[]>([])
// 跟踪已加载的节点ID
const loadedKeys = ref<Set<number>>(new Set())
// 跟踪正在加载的父节点ID
const loadingKeys = ref<Set<number>>(new Set())

// 查询参数
const queryParams = reactive<FunctionQueryDTO>({
  functionName: undefined,
  functionType: undefined,
  status: undefined,
  visible: undefined,
  scene: 'admin', // 默认为 admin 场景
})

// 弹窗状态
const formVisible = ref(false)

// 当前操作的功能
const currentFunctionId = ref<number>()
const currentParentId = ref<number>()
const currentParentScene = ref<string>()

// 检查是否有查询条件（排除 scene，因为 scene 是默认值且通过 listLazy 处理）
const hasQueryConditions = () => {
  return !!(
    (
      queryParams.functionName ||
      queryParams.functionType ||
      queryParams.status !== undefined ||
      queryParams.visible !== undefined
    )
    // 注意：scene 不作为查询条件判断，始终使用 listLazy
  )
}

// 获取功能列表
const getList = async () => {
  loading.value = true
  loadedKeys.value.clear()
  expendedRowKeys.value = []

  try {
    if (hasQueryConditions()) {
      // 有查询条件时，使用 list 接口一次性加载全部数据（按 scene 筛选）
      const res = await getFunctionList(queryParams)
      if (res.code === 200) {
        functionList.value = res.data || []
      }
    } else {
      // 无查询条件时，使用异步加载模式，只加载顶层（始终使用 listLazy）
      const res = await getFunctionListLazy(0, queryParams.scene)
      if (res.code === 200) {
        functionList.value = res.data || []
      }
    }
  } catch (_e) {
    message.error(t('system.function.getFunctionListFailed'))
  } finally {
    loading.value = false
  }
}

// 搜索功能
const handleQuery = () => {
  getList()
}

// 重置查询
const resetQuery = () => {
  queryParams.functionName = undefined
  queryParams.functionType = undefined
  queryParams.status = undefined
  queryParams.visible = undefined
  queryParams.scene = 'admin' // 重置为默认值
  getList()
}

// 递归加载并展开所有节点的辅助函数
const expandAllNodes = async (nodes: FunctionTreeVO[]): Promise<void> => {
  for (const node of nodes) {
    // 检查节点是否有子节点但还没加载 children
    if (node.hasChildren && !loadedKeys.value.has(node.functionId)) {
      loadingKeys.value.add(node.functionId)
      try {
        const res = await getFunctionListLazy(node.functionId)
        if (res.code === 200) {
          const children = res.data || []
          if (children.length > 0) {
            node.children = children
          } else {
            delete node.children
          }
          // 标记该节点的 children 已加载（无论是否为空）
          loadedKeys.value.add(node.functionId)
        }
      } catch (_e) {
        // 忽略错误，继续处理其他节点
      } finally {
        loadingKeys.value.delete(node.functionId)
      }
    }

    // 添加到展开列表
    if (!expendedRowKeys.value.includes(node.functionId)) {
      expendedRowKeys.value.push(node.functionId)
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
    await expandAllNodes(functionList.value)
  } else {
    // 折叠所有节点
    expendedRowKeys.value = []
  }
}

// 展开/折叠指定行（支持异步加载子节点）
const toggleExpandRow = async (expanded: boolean, record: FunctionTreeVO) => {
  if (expanded) {
    // 展开时，检查是否需要加载子节点（未加载过且有子节点时才加载）
    if (!loadedKeys.value.has(record.functionId) && record.hasChildren) {
      // 标记为加载中
      loadingKeys.value.add(record.functionId)
      try {
        const res = await getFunctionListLazy(record.functionId)
        if (res.code === 200) {
          const children = res.data || []
          // 查找并更新父节点的 children
          const updateNode = (list: FunctionTreeVO[]): boolean => {
            for (const node of list) {
              if (node.functionId === record.functionId) {
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
          updateNode(functionList.value)
          // 标记该节点的 children 已加载
          loadedKeys.value.add(record.functionId)
        }
      } catch (_e) {
        message.error(t('system.function.loadChildNodesFailed'))
      } finally {
        // 移除加载中标记
        loadingKeys.value.delete(record.functionId)
      }
    }
    // 添加到展开列表
    expendedRowKeys.value = [...expendedRowKeys.value, record.functionId]
  } else {
    // 折叠时，递归收集所有子孙节点ID
    const collectChildIds = (node: FunctionTreeVO, ids: number[] = []) => {
      if (node.children) {
        for (const child of node.children) {
          ids.push(child.functionId)
          collectChildIds(child, ids)
        }
      }
      return ids
    }
    const childIds = collectChildIds(record)
    // 从展开列表中移除当前节点及所有子孙节点
    expendedRowKeys.value = expendedRowKeys.value.filter((id) => id !== record.functionId && !childIds.includes(id))
  }
}

// 新增功能
const handleAdd = () => {
  currentFunctionId.value = undefined
  currentParentId.value = 0
  currentParentScene.value = queryParams.scene
  formVisible.value = true
}

// 新增子功能
const handleAddChild = (record: FunctionTreeVO) => {
  currentFunctionId.value = undefined
  currentParentId.value = record.functionId
  currentParentScene.value = record.scene
  formVisible.value = true
}

// 修改功能
const handleUpdate = (record: FunctionTreeVO) => {
  currentFunctionId.value = record.functionId
  currentParentId.value = undefined
  formVisible.value = true
}

// 删除功能
const handleDelete = (record: FunctionTreeVO) => {
  Modal.confirm({
    title: t('common.systemTip'),
    content: t('system.function.deleteFunctionConfirm', { functionName: record.functionName }),
    onOk: async () => {
      try {
        const res = await deleteFunction(String(record.functionId))
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

// 初始化
onMounted(() => {
  getList()
})
</script>

<style scoped>
.actions-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  gap: 16px;
}

.actions-filter {
  flex-shrink: 0;
}

.function-management {
  padding: 16px;

  .search-card {
    margin-bottom: 16px;
  }

  .table-card {
    :deep(.ant-card-body) {
      padding: 0;
    }
  }
}

@media (max-width: 768px) {
  .actions-container {
    flex-direction: column;
    align-items: stretch;
  }

  .actions-filter {
    width: 100%;
  }
}
</style>
