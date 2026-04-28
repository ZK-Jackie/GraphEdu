<template>
  <a-drawer
    :open="visible"
    :title="`${t('system.dict.dictData')}: ${dictType}`"
    width="70%"
    placement="right"
    @close="handleClose"
  >
    <!-- 搜索表单 -->
    <a-card :bordered="false" class="search-card">
      <a-form layout="inline" :model="queryParams">
        <a-form-item :label="t('system.dict.dictLabel')">
          <a-input
            v-model:value="queryParams.dictLabel"
            :placeholder="t('system.dict.dictLabelPlaceholder')"
            allow-clear
            style="width: 200px"
            @press-enter="handleQuery"
          />
        </a-form-item>
        <a-form-item :label="t('common.status')">
          <a-select
            v-model:value="queryParams.status"
            :placeholder="t('system.dict.statusPlaceholder')"
            allow-clear
            style="width: 150px"
          >
            <a-select-option value="0">{{ t('common.normal') }}</a-select-option>
            <a-select-option value="1">{{ t('common.disabled') }}</a-select-option>
          </a-select>
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

    <!-- 操作按钮和表格 -->
    <a-card :bordered="false" class="table-card">
      <!-- 操作按钮 -->
      <template #title>
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
        </a-space>
      </template>

      <!-- 字典数据表格 -->
      <a-table
        :columns="columns"
        :data-source="dataList"
        :loading="loading"
        :row-selection="rowSelection"
        :pagination="false"
        row-key="dictCode"
      >
        <template #bodyCell="{ column, record }">
          <!-- 字典标签列 - 带样式 -->
          <template v-if="column.key === 'dictLabel'">
            <span v-if="!record.listClass || record.listClass === 'default'" :class="record.cssClass">
              {{ record.dictLabel }}
            </span>
            <a-tag v-else :color="getTagColor(record.listClass)" :class="record.cssClass">
              {{ record.dictLabel }}
            </a-tag>
          </template>
          <!-- 状态列 -->
          <template v-else-if="column.key === 'status'">
            <DictTag :options="sys_data_status" :value="record.status" />
          </template>
          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-tooltip :title="t('common.edit')">
                <a-button type="link" size="small" @click="handleUpdate(record as DictDataListVO)">
                  <template #icon><EditOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip :title="t('common.delete')">
                <a-button type="link" size="small" danger @click="handleDelete(record as DictDataListVO)">
                  <template #icon><DeleteOutlined /></template>
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

      <!-- 分页 -->
      <div class="pagination-container">
        <a-pagination
          v-model:current="queryParams.page"
          v-model:page-size="queryParams.size"
          :total="total"
          :show-size-changer="true"
          :show-total="showTotal"
          @change="handlePageChange"
        />
      </div>
    </a-card>

    <!-- 字典数据表单弹窗 -->
    <DictDataForm
      v-model:visible="formVisible"
      :dict-code="currentDictCode"
      :dict-type="dictType"
      @success="handleFormSuccess"
    />
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { SearchOutlined, ReloadOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import type { TableProps } from 'ant-design-vue'
import { getDictDataList, deleteDictData } from '@/api/system/dict.ts'
import type { DictDataQueryDTO, DictDataListVO } from '@/types/api/system/dict.ts'
import { useDict } from '@/utils/dict.ts'
import { parseTime } from '@/utils/common.ts'
import useDictStore from '@/stores/modules/dict.ts'
import DictTag from '../../../../../components/dict/DictTag.vue'
import DictDataForm from './DictDataForm.vue'

const { t } = useI18n()

interface Props {
  visible: boolean
  dictId: number
  dictType: string
}

interface Emits {
  (e: 'update:visible', value: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 获取字典数据
const { sys_data_status } = useDict('sys_data_status')

// 表格列定义
const columns: TableProps['columns'] = [
  { title: t('system.dict.dictCode'), dataIndex: 'dictCode', key: 'dictCode', width: 100 },
  { title: t('system.dict.dictLabel'), dataIndex: 'dictLabel', key: 'dictLabel', width: 150 },
  { title: t('system.dict.dictValue'), dataIndex: 'dictValue', key: 'dictValue', width: 120 },
  { title: t('system.dict.dictSort'), dataIndex: 'dictSort', key: 'dictSort', width: 100 },
  { title: t('common.status'), dataIndex: 'status', key: 'status', width: 100 },
  { title: t('common.remark'), dataIndex: 'remark', key: 'remark', ellipsis: true },
  { title: t('common.createTime'), dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: t('common.operation'), key: 'action', fixed: 'right', width: 120 },
]

// 数据状态
const loading = ref(false)
const dataList = ref<DictDataListVO[]>([])
const total = ref(0)

// 查询参数
const queryParams = reactive<DictDataQueryDTO>({
  page: 1,
  size: 10,
  dictType: props.dictType,
  dictLabel: undefined,
  status: undefined,
})

// 选中的行
const selectedRowKeys = ref<(string | number)[]>([])
const selectedRows = ref<DictDataListVO[]>([])
const single = computed(() => selectedRowKeys.value.length !== 1)
const multiple = computed(() => selectedRowKeys.value.length === 0)

// 行选择配置
const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: any[], rows: any[]) => {
    selectedRowKeys.value = keys
    selectedRows.value = rows as DictDataListVO[]
  },
}))

// 弹窗状态
const formVisible = ref(false)
const currentDictCode = ref<number>()

// 获取字典数据列表
const getList = async () => {
  loading.value = true
  queryParams.dictType = props.dictType
  try {
    const res = await getDictDataList(queryParams)
    if (res.code === 200) {
      dataList.value = res.data.rows || []
      total.value = res.data.total || 0
    }
  } catch (_error) {
    message.error(t('system.dict.getDictDataListFailed'))
  } finally {
    loading.value = false
  }
}

// 分页组件的 show-total 回调
const showTotal = (total: number) => `${t('common.total')} ${total} ${t('common.items')}`

// 搜索
const handleQuery = () => {
  queryParams.page = 1
  getList()
}

// 重置查询
const resetQuery = () => {
  queryParams.dictLabel = undefined
  queryParams.status = undefined
  queryParams.page = 1
  getList()
}

// 分页变化
const handlePageChange = () => {
  getList()
}

// 新增
const handleAdd = () => {
  currentDictCode.value = undefined
  formVisible.value = true
}

// 修改
const handleUpdate = (record?: DictDataListVO) => {
  if (record) {
    currentDictCode.value = record.dictCode
  } else if (selectedRows.value.length === 1) {
    const dictCode = selectedRows.value[0]?.dictCode
    if (dictCode !== undefined) {
      currentDictCode.value = dictCode
    }
  }
  formVisible.value = true
}

// 删除
const handleDelete = (record?: DictDataListVO) => {
  let dictCodes: string
  if (record) {
    dictCodes = String(record.dictCode)
  } else {
    dictCodes = selectedRowKeys.value.join(',')
  }

  Modal.confirm({
    title: t('common.systemTip'),
    content: t('common.deleteConfirm'),
    onOk: async () => {
      try {
        const res = await deleteDictData(dictCodes)
        if (res.code === 200) {
          message.success(t('common.deleteSuccess'))
          // 清空本地缓存
          useDictStore().removeDict(props.dictType)
          getList()
        }
      } catch (_error) {
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

// 获取 Tag 颜色
const getTagColor = (listClass: string) => {
  const colorMap: Record<string, string> = {
    primary: 'blue',
    success: 'green',
    info: 'cyan',
    warning: 'orange',
    danger: 'red',
    default: 'default',
  }
  return colorMap[listClass] || 'default'
}

// 表单提交成功
const handleFormSuccess = () => {
  formVisible.value = false
  // 清空本地缓存
  useDictStore().removeDict(props.dictType)
  getList()
}

// 关闭抽屉
const handleClose = () => {
  emit('update:visible', false)
}

// 监听 visible 变化，打开时加载数据
watch(
  () => props.visible,
  (val) => {
    if (val) {
      // 重置查询参数
      queryParams.dictLabel = undefined
      queryParams.status = undefined
      queryParams.page = 1
      selectedRowKeys.value = []
      selectedRows.value = []
      getList()
    }
  }
)
</script>

<style scoped>
.search-card {
  margin-bottom: 16px;
}

.table-card {
  :deep(.ant-card-body) {
    padding: 0;
  }
}

.pagination-container {
  padding: 16px;
  display: flex;
  justify-content: flex-end;
}

:deep(.ant-drawer-body) {
  padding: 16px;
}
</style>
