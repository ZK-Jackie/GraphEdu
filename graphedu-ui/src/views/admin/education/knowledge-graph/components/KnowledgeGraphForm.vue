<template>
  <a-modal
    :visible="visible"
    :title="isEdit ? '修改知识图谱' : '新增知识图谱'"
    :confirm-loading="loading"
    :width="600"
    @cancel="handleCancel"
    @ok="handleSubmit"
  >
    <a-form ref="formRef" :model="formState" :rules="rules as any" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
      <a-form-item label="书籍ID" name="bookId">
        <a-input-number v-model:value="formState.bookId" placeholder="请输入书籍ID" :min="1" style="width: 100%" />
      </a-form-item>

      <a-form-item label="图谱名称" name="graphName">
        <a-input v-model:value="formState.graphName" placeholder="请输入图谱名称" allow-clear />
      </a-form-item>

      <a-form-item label="数据库名称" name="graphDatabase">
        <a-input v-model:value="formState.graphDatabase" placeholder="请输入Neo4j数据库名称" allow-clear />
      </a-form-item>

      <a-form-item v-if="isEdit" label="版本号" name="version">
        <a-input v-model:value="formState.version" placeholder="请输入版本号" allow-clear />
      </a-form-item>

      <a-form-item label="构建方法" name="buildMethod">
        <a-select v-model:value="formState.buildMethod" placeholder="请选择构建方法" allow-clear>
          <a-select-option value="nlp">NLP</a-select-option>
          <a-select-option value="llm">LLM</a-select-option>
          <a-select-option value="llm_assisted">LLM辅助</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="图谱描述" name="description">
        <a-textarea v-model:value="formState.description" placeholder="请输入图谱描述" :rows="4" allow-clear />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { message } from 'ant-design-vue'
import type { FormInstance } from 'ant-design-vue'
import { addKnowledgeGraph, updateKnowledgeGraph, getKnowledgeGraphDetail } from '@/api/education/knowledge-graph.ts'
import type { KnowledgeGraphCreateDTO, KnowledgeGraphUpdateDTO } from '@/types/api/knowledge-graph'

interface Props {
  visible: boolean
  graphId?: number
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const isEdit = computed(() => !!props.graphId)

const formRef = ref<FormInstance>()
const loading = ref(false)

// 表单状态
const formState = reactive({
  bookId: undefined as number | undefined,
  graphName: '',
  graphDatabase: '',
  version: '1.0.0',
  buildMethod: undefined as string | undefined,
  description: '',
})

// 表单验证规则
const rules = {
  bookId: [{ required: true, message: '请输入书籍ID' }],
  graphName: [{ required: true, message: '请输入图谱名称' }],
  graphDatabase: [{ required: true, message: '请输入数据库名称' }],
  buildMethod: [{ required: true, message: '请选择构建方法' }],
}

// 获取知识图谱详情
const getDetail = async () => {
  if (!props.graphId) return
  loading.value = true
  try {
    const res = await getKnowledgeGraphDetail(props.graphId)
    if (res.code === 200 && res.data) {
      Object.assign(formState, {
        bookId: res.data.bookId,
        graphName: res.data.graphName,
        graphDatabase: res.data.graphDatabase,
        version: res.data.version,
        buildMethod: res.data.buildMethod,
        description: res.data.description,
      })
    }
  } catch (_e) {
    message.error('获取知识图谱详情失败')
  } finally {
    loading.value = false
  }
}

// 关闭弹窗
const handleCancel = () => {
  emit('update:visible', false)
  resetForm()
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(formState, {
    bookId: undefined,
    graphName: '',
    graphDatabase: '',
    version: '1.0.0',
    buildMethod: undefined,
    description: '',
  })
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
  } catch (_e) {
    return
  }

  loading.value = true
  try {
    if (isEdit.value) {
      // 修改
      const data: KnowledgeGraphUpdateDTO = {
        graphId: props.graphId!,
        bookId: formState.bookId,
        graphName: formState.graphName || undefined,
        graphDatabase: formState.graphDatabase || undefined,
        version: formState.version,
        buildMethod: formState.buildMethod,
        description: formState.description,
      }
      const res = await updateKnowledgeGraph(data)
      if (res.code === 200) {
        message.success('修改成功')
        emit('success')
        handleCancel()
      }
    } else {
      // 新增
      const data: KnowledgeGraphCreateDTO = {
        courseId: 0,
        bookId: formState.bookId!,
        graphName: formState.graphName,
        graphDatabase: formState.graphDatabase,
        buildMethod: formState.buildMethod,
        description: formState.description,
      }
      const res = await addKnowledgeGraph(data)
      if (res.code === 200) {
        message.success('新增成功')
        emit('success')
        handleCancel()
      }
    }
  } catch (_e) {
    message.error(isEdit.value ? '修改失败' : '新增失败')
  } finally {
    loading.value = false
  }
}

// 监听弹窗显示状态
watch(
  () => props.visible,
  (val) => {
    if (val && isEdit.value) {
      getDetail()
    } else if (!val) {
      resetForm()
    }
  }
)
</script>
