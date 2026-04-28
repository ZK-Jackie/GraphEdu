<template>
  <div class="gen-edit">
    <a-card :loading="loading">
      <a-tabs v-model:active-key="activeTab">
        <!-- 基本信息 -->
        <a-tab-pane key="basic" tab="基本信息">
          <a-form ref="basicFormRef" :model="info" :rules="basicRules as any" :label-col="{ span: 6 }">
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="表名称" name="tableName">
                  <a-input v-model:value="info.tableName" placeholder="请输入表名称" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="表描述" name="tableComment">
                  <a-input v-model:value="info.tableComment" placeholder="请输入表描述" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="实体类名称" name="className">
                  <a-input v-model:value="info.className" placeholder="请输入实体类名称" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="作者" name="functionAuthor">
                  <a-input v-model:value="info.functionAuthor" placeholder="请输入作者" />
                </a-form-item>
              </a-col>
              <a-col :span="24">
                <a-form-item label="备注" name="remark" :label-col="{ span: 2 }">
                  <a-textarea v-model:value="info.remark" :rows="3" placeholder="请输入备注" />
                </a-form-item>
              </a-col>
            </a-row>
          </a-form>
        </a-tab-pane>

        <!-- 字段信息 -->
        <a-tab-pane key="columnInfo" tab="字段信息">
          <a-table
            :data-source="columns"
            :pagination="false"
            :scroll="{ x: 1500, y: 400 }"
            row-key="columnId"
            size="small"
          >
            <a-table-column key="index" title="序号" width="60" align="center">
              <template #default="{ index }">{{ index + 1 }}</template>
            </a-table-column>
            <a-table-column title="字段列名" data-index="columnName" width="120" />
            <a-table-column title="字段描述" width="120">
              <template #default="{ record }">
                <a-input v-model:value="record.columnComment" size="small" />
              </template>
            </a-table-column>
            <a-table-column title="物理类型" data-index="columnType" width="100" />
            <a-table-column title="Python类型" width="120">
              <template #default="{ record }">
                <a-select v-model:value="record.pythonType" size="small" style="width: 100%">
                  <a-select-option value="int">int</a-select-option>
                  <a-select-option value="str">str</a-select-option>
                  <a-select-option value="float">float</a-select-option>
                  <a-select-option value="datetime">datetime</a-select-option>
                  <a-select-option value="bool">bool</a-select-option>
                  <a-select-option value="Decimal">Decimal</a-select-option>
                </a-select>
              </template>
            </a-table-column>
            <a-table-column title="Python属性" width="120">
              <template #default="{ record }">
                <a-input v-model:value="record.pythonField" size="small" />
              </template>
            </a-table-column>
            <a-table-column title="插入" width="60" align="center">
              <template #default="{ record }">
                <a-checkbox v-model:checked="record.isInsert" :true-value="'1'" :false-value="'0'" />
              </template>
            </a-table-column>
            <a-table-column title="编辑" width="60" align="center">
              <template #default="{ record }">
                <a-checkbox v-model:checked="record.isEdit" :true-value="'1'" :false-value="'0'" />
              </template>
            </a-table-column>
            <a-table-column title="列表" width="60" align="center">
              <template #default="{ record }">
                <a-checkbox v-model:checked="record.isList" :true-value="'1'" :false-value="'0'" />
              </template>
            </a-table-column>
            <a-table-column title="查询" width="60" align="center">
              <template #default="{ record }">
                <a-checkbox v-model:checked="record.isQuery" :true-value="'1'" :false-value="'0'" />
              </template>
            </a-table-column>
            <a-table-column title="查询方式" width="100">
              <template #default="{ record }">
                <a-select v-model:value="record.queryType" size="small" style="width: 100%">
                  <a-select-option value="EQ">=</a-select-option>
                  <a-select-option value="NE">!=</a-select-option>
                  <a-select-option value="GT">></a-select-option>
                  <a-select-option value="GTE">>=</a-select-option>
                  <a-select-option value="LT"><</a-select-option>
                  <a-select-option value="LTE"><=</a-select-option>
                  <a-select-option value="LIKE">LIKE</a-select-option>
                  <a-select-option value="BETWEEN">BETWEEN</a-select-option>
                </a-select>
              </template>
            </a-table-column>
            <a-table-column title="必填" width="60" align="center">
              <template #default="{ record }">
                <a-checkbox v-model:checked="record.isRequired" :true-value="'1'" :false-value="'0'" />
              </template>
            </a-table-column>
            <a-table-column title="显示类型" width="130">
              <template #default="{ record }">
                <a-select v-model:value="record.htmlType" size="small" style="width: 120px">
                  <a-select-option value="input">文本框</a-select-option>
                  <a-select-option value="textarea">文本域</a-select-option>
                  <a-select-option value="select">下拉框</a-select-option>
                  <a-select-option value="radio">单选框</a-select-option>
                  <a-select-option value="checkbox">复选框</a-select-option>
                  <a-select-option value="datetime">日期控件</a-select-option>
                  <a-select-option value="imageUpload">图片上传</a-select-option>
                  <a-select-option value="fileUpload">文件上传</a-select-option>
                  <a-select-option value="editor">富文本控件</a-select-option>
                </a-select>
              </template>
            </a-table-column>
            <a-table-column title="字典类型" width="150">
              <template #default="{ record }">
                <a-select
                  v-model:value="record.dictType"
                  size="small"
                  allow-clear
                  show-search
                  :filter-option="filterDictOption"
                  style="width: 140px"
                >
                  <a-select-option v-for="dict in dictOptions" :key="dict.dictType" :value="dict.dictType">
                    <span style="float: left">{{ dict.dictName }}</span>
                    <span style="float: right; color: #8492a6; font-size: 12px">
                      {{ dict.dictType }}
                    </span>
                  </a-select-option>
                </a-select>
              </template>
            </a-table-column>
          </a-table>
        </a-tab-pane>

        <!-- 生成信息 -->
        <a-tab-pane key="genInfo" tab="生成信息">
          <a-form ref="genFormRef" :model="info" :rules="genRules as any" :label-col="{ span: 8 }">
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="生成模板" name="tplCategory">
                  <a-select v-model:value="info.tplCategory" @change="(val: any) => handleTplChange(val)">
                    <a-select-option value="crud">单表（增删改查）</a-select-option>
                    <a-select-option value="tree">树表（增删改查）</a-select-option>
                    <a-select-option value="sub">主子表（增删改查）</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="前端类型" name="tplWebType">
                  <a-select v-model:value="info.tplWebType">
                    <a-select-option value="ant-design-vue">Vue3 Ant Design Vue 模板</a-select-option>
                    <a-select-option value="element-plus">Vue3 Element Plus 模板</a-select-option>
                    <a-select-option value="element-ui">Vue2 Element UI 模板</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="生成包路径" name="packageName">
                  <a-input v-model:value="info.packageName" placeholder="如: com.graphedu.system" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="生成模块名" name="moduleName">
                  <a-input v-model:value="info.moduleName" placeholder="如: system" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="生成业务名" name="businessName">
                  <a-input v-model:value="info.businessName" placeholder="如: user" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="生成功能名" name="functionName">
                  <a-input v-model:value="info.functionName" placeholder="如: 用户" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="生成代码方式" name="genType">
                  <a-radio-group v-model:value="info.genType">
                    <a-radio value="0">zip压缩包</a-radio>
                    <a-radio value="1">自定义路径</a-radio>
                  </a-radio-group>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="上级菜单">
                  <a-tree-select
                    v-model:value="info.parentMenuId"
                    :tree-data="menuOptions"
                    :field-names="{ label: 'functionName', value: 'functionId', children: 'children' }"
                    placeholder="请选择系统菜单"
                    tree-default-expand-all
                    allow-clear
                  />
                </a-form-item>
              </a-col>
              <a-col v-if="info.genType === '1'" :span="24">
                <a-form-item label="自定义路径" name="genPath" :label-col="{ span: 4 }">
                  <a-input v-model:value="info.genPath" placeholder="填写磁盘绝对路径，若不填写，则生成到当前项目下">
                    <template #addonAfter>
                      <a-dropdown>
                        <a-button type="primary" size="small">
                          快速选择
                          <DownOutlined />
                        </a-button>
                        <template #overlay>
                          <a-menu @click="handleGenPathClick">
                            <a-menu-item key="/">恢复默认的生成基础路径</a-menu-item>
                          </a-menu>
                        </template>
                      </a-dropdown>
                    </template>
                  </a-input>
                </a-form-item>
              </a-col>
            </a-row>

            <!-- 树表配置 -->
            <template v-if="info.tplCategory === 'tree'">
              <a-divider />
              <h4>树表配置</h4>
              <a-row :gutter="16">
                <a-col :span="8">
                  <a-form-item label="树编码字段">
                    <a-select v-model:value="info.treeCode" placeholder="请选择">
                      <a-select-option v-for="(column, index) in columns" :key="index" :value="column.columnName">
                        {{ column.columnName }}：{{ column.columnComment }}
                      </a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="树父编码字段">
                    <a-select v-model:value="info.treeParentCode" placeholder="请选择">
                      <a-select-option v-for="(column, index) in columns" :key="index" :value="column.columnName">
                        {{ column.columnName }}：{{ column.columnComment }}
                      </a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="树名称字段">
                    <a-select v-model:value="info.treeName" placeholder="请选择">
                      <a-select-option v-for="(column, index) in columns" :key="index" :value="column.columnName">
                        {{ column.columnName }}：{{ column.columnComment }}
                      </a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
              </a-row>
            </template>

            <!-- 主子表配置 -->
            <template v-if="info.tplCategory === 'sub'">
              <a-divider />
              <h4>主子表配置</h4>
              <a-row :gutter="16">
                <a-col :span="12">
                  <a-form-item label="关联子表的表名">
                    <a-select v-model:value="info.subTableName" placeholder="请选择" @change="(val: any) => handleSubTableChange(val)">
                      <a-select-option v-for="(table, index) in tables" :key="index" :value="table.tableName">
                        {{ table.tableName }}：{{ table.tableComment }}
                      </a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="子表关联的外键名">
                    <a-select v-model:value="info.subTableFkName" placeholder="请选择">
                      <a-select-option v-for="(column, index) in subColumns" :key="index" :value="column.columnName">
                        {{ column.columnName }}：{{ column.columnComment }}
                      </a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
              </a-row>
            </template>
          </a-form>
        </a-tab-pane>
      </a-tabs>

      <!-- 底部按钮 -->
      <div style="text-align: center; margin-top: 24px">
        <a-space>
          <a-button type="primary" @click="submitForm">提交</a-button>
          <a-button @click="goBack">返回</a-button>
        </a-space>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { DownOutlined } from '@ant-design/icons-vue'
import { getGenTableDetail, updateGenTable, getDictOptionSelect, getMenuTreeSelect } from '@/api/system/tool/gen'
import type { GenTableVO, GenTableColumnVO, DictOptionVO, MenuTreeOptionVO } from '@/types/api/tool/gen.ts'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const activeTab = ref('columnInfo')
const columns = ref<GenTableColumnVO[]>([])
const dictOptions = ref<DictOptionVO[]>([])
const menuOptions = ref<MenuTreeOptionVO[]>([])
const tables = ref<GenTableVO[]>([])
const subColumns = ref<GenTableColumnVO[]>([])

const info = reactive<GenTableVO>({
  tableName: '',
  tableComment: '',
  className: '',
  functionAuthor: '',
  remark: '',
  tplCategory: 'crud',
  tplWebType: 'ant-design-vue',
  packageName: '',
  moduleName: '',
  businessName: '',
  functionName: '',
  genType: '0',
  genPath: '',
  parentMenuId: undefined,
  treeCode: '',
  treeParentCode: '',
  treeName: '',
  subTableName: '',
  subTableFkName: '',
})

const basicRules = {
  tableName: [{ required: true, message: '请输入表名称', trigger: 'blur' }],
  tableComment: [{ required: true, message: '请输入表描述', trigger: 'blur' }],
  className: [{ required: true, message: '请输入实体类名称', trigger: 'blur' }],
  functionAuthor: [{ required: true, message: '请输入作者', trigger: 'blur' }],
}

const genRules = {
  tplCategory: [{ required: true, message: '请选择生成模板', trigger: 'change' }],
  packageName: [{ required: true, message: '请输入生成包路径', trigger: 'blur' }],
  moduleName: [{ required: true, message: '请输入生成模块名', trigger: 'blur' }],
  businessName: [{ required: true, message: '请输入生成业务名', trigger: 'blur' }],
  functionName: [{ required: true, message: '请输入生成功能名', trigger: 'blur' }],
}

const basicFormRef = ref()
const genFormRef = ref()

/** 提交按钮 */
async function submitForm() {
  try {
    await Promise.all([basicFormRef.value?.validate(), genFormRef.value?.validate()])

    const genTable: any = { ...info }
    genTable.columns = columns.value
    genTable.params = {
      treeCode: info.treeCode,
      treeParentCode: info.treeParentCode,
      treeName: info.treeName,
      parentMenuId: info.parentMenuId,
    }

    await updateGenTable(genTable)
    message.success('修改成功')
    goBack()
  } catch (error) {
    console.error('表单校验失败', error)
  }
}

/** 返回 */
function goBack() {
  router.push({
    path: '/tool/gen',
    query: { pageNum: route.query.pageNum },
  })
}

/** 过滤字典选项 */
function filterDictOption(input: string, option: any) {
  return option.children[0].children.toLowerCase().indexOf(input.toLowerCase()) >= 0
}

/** 模板类型变化 */
function handleTplChange(value: string) {
  if (value !== 'sub') {
    info.subTableName = ''
    info.subTableFkName = ''
  }
}

/** 自定义路径快速选择 */
function handleGenPathClick({ key }: any) {
  if (key === '/') {
    info.genPath = '/'
  }
}

/** 子表变化 */
function handleSubTableChange(tableName: string) {
  info.subTableFkName = ''
  const table = tables.value.find((t) => t.tableName === tableName)
  if (table) {
    subColumns.value = table.columns || []
  }
}

/** 获取表详细信息 */
function loadTableDetail() {
  const tableId = Number(route.params.tableId)
  if (!tableId) return

  loading.value = true
  getGenTableDetail(tableId)
    .then((res) => {
      const data = res.data
      columns.value = data.rows || []
      tables.value = data.tables || []

      // 填充表信息
      Object.assign(info, data.info)

      // 处理 params
      if (data.info.params) {
        Object.assign(info, data.info.params)
      }
    })
    .finally(() => {
      loading.value = false
    })

  // 获取字典选项
  getDictOptionSelect().then((res) => {
    dictOptions.value = res.data || []
  })

  // 获取菜单树
  getMenuTreeSelect().then((res) => {
    menuOptions.value = res.data || []
  })
}

onMounted(() => {
  loadTableDetail()
})
</script>

<style scoped>
.gen-edit {
  padding: 16px;
}
</style>
