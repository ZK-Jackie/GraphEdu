<template>
  <a-modal v-model:open="visible" title="导入表" width="800px" :footer="null" :destroy-on-close="true">
    <a-form layout="inline" style="margin-bottom: 16px">
      <a-form-item label="表名称">
        <a-input
          v-model:value="queryParams.tableName"
          placeholder="请输入表名称"
          allow-clear
          style="width: 180px"
          @press-enter="handleQuery"
        />
      </a-form-item>
      <a-form-item label="表描述">
        <a-input
          v-model:value="queryParams.tableComment"
          placeholder="请输入表描述"
          allow-clear
          style="width: 180px"
          @press-enter="handleQuery"
        />
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

    <a-table
      :row-selection="rowSelection as any"
      :data-source="dbTableList"
      :loading="loading"
      :pagination="false"
      :scroll="{ y: 260 }"
      row-key="tableName"
      @row-click="clickRow"
    >
      <a-table-column title="表名称" data-index="tableName" :ellipsis="true" />
      <a-table-column title="表描述" data-index="tableComment" :ellipsis="true" />
      <a-table-column title="创建时间" data-index="createTime">
        <template #default="{ text }">{{ parseTime(text) }}</template>
      </a-table-column>
      <a-table-column title="更新时间" data-index="updateTime">
        <template #default="{ text }">{{ parseTime(text) }}</template>
      </a-table-column>
    </a-table>

    <div style="margin-top: 16px; text-align: right">
      <a-pagination
        v-show="total > 0"
        v-model:current="queryParams.page"
        v-model:page-size="queryParams.size"
        :total="total"
        :show-total="(total) => `共 ${total} 条`"
        size="small"
        @change="getList"
      />
    </div>

    <div style="margin-top: 16px; text-align: center">
      <a-space>
        <a-button type="primary" @click="handleImportTable">确定</a-button>
        <a-button @click="visible = false">取消</a-button>
      </a-space>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { message } from 'ant-design-vue'
import type { TableProps } from 'ant-design-vue'
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { getDbTableList, importTable } from '@/api/system/tool/gen'
import type { DbTableQueryDTO, DbTableVO } from '@/types/api/tool/gen.ts'
import { parseTime } from '@/utils/common.ts'

const emit = defineEmits<{
  ok: []
}>()

const visible = ref(false)
const loading = ref(false)
const selectedTableNames = ref<string[]>([])
const dbTableList = ref<DbTableVO[]>([])
const total = ref(0)

const queryParams = reactive<DbTableQueryDTO>({
  page: 1,
  size: 10,
  tableName: undefined,
  tableComment: undefined,
})

const rowSelection = computed(() => ({
  selectedRowKeys: selectedTableNames.value,
  onChange: (keys: string[]) => {
    selectedTableNames.value = keys
  },
}) as any)

/** 显示弹窗 */
function show() {
  getList()
  visible.value = true
}

/** 单击选择行 */
function clickRow(record: DbTableVO) {
  const tableName = record.tableName || ''
  const index = selectedTableNames.value.indexOf(tableName)
  if (index > -1) {
    selectedTableNames.value.splice(index, 1)
  } else {
    selectedTableNames.value.push(tableName)
  }
}

/** 查询数据库表列表 */
function getList() {
  loading.value = true
  getDbTableList(queryParams)
    .then((res) => {
      dbTableList.value = res.data.rows || []
      total.value = res.data.total || 0
    })
    .finally(() => {
      loading.value = false
    })
}

/** 搜索按钮操作 */
function handleQuery() {
  queryParams.page = 1
  getList()
}

/** 重置按钮操作 */
function resetQuery() {
  queryParams.tableName = undefined
  queryParams.tableComment = undefined
  handleQuery()
}

/** 导入按钮操作 */
function handleImportTable() {
  if (!selectedTableNames.value.length) {
    message.warning('请选择要导入的表')
    return
  }
  importTable({ tableNames: selectedTableNames.value.join(',') })
    .then((res) => {
      message.success(res.msg || '导入成功')
      if (res.code === 200) {
        visible.value = false
        emit('ok')
      }
    })
    .catch(() => {})
}

defineExpose({
  show,
})
</script>
