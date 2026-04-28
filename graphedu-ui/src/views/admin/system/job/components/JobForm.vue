<template>
  <a-modal
    :open="visible"
    :title="isEdit ? t('system.job.editJob') : t('system.job.addJob')"
    :width="700"
    :confirm-loading="loading"
    @ok="handleSubmit"
    @cancel="handleCancel"
  >
    <a-form ref="formRef" :model="form" :rules="rules as any" :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }">
      <a-form-item :label="t('system.job.jobName')" name="jobName">
        <a-input v-model:value="form.jobName" :placeholder="t('system.job.jobNamePlaceholder')" />
      </a-form-item>

      <a-form-item :label="t('system.job.jobGroup')" name="jobGroup">
        <DictSelect
          v-model:model-value="form.jobGroup"
          dict-type="sys_job_group"
          :placeholder="t('system.job.jobGroupPlaceholder')"
        />
      </a-form-item>

      <a-form-item :label="t('system.job.jobExecutor')" name="jobExecutor">
        <DictSelect
          v-model:model-value="form.jobExecutor"
          dict-type="sys_job_executor"
          :placeholder="t('system.job.jobExecutorPlaceholder')"
          @change="handleExecutorChange"
        />
      </a-form-item>

      <a-form-item :label="t('system.job.invokeTarget')" name="invokeTarget">
        <a-textarea
          v-model:value="form.invokeTarget"
          :placeholder="targetPlaceholder"
          :rows="2"
          :maxlength="512"
          show-count
        />
      </a-form-item>

      <a-form-item :label="t('system.job.cronExpression')" name="cronExpression">
        <a-input-group compact>
          <a-input
            v-model:value="form.cronExpression"
            :placeholder="t('system.job.cronExpressionPlaceholder')"
            style="width: calc(100% - 90px)"
          />
          <a-button @click="cronVisible = true">
            <template #icon><FieldTimeOutlined /></template>
            {{ t('system.job.generateCron') }}
          </a-button>
        </a-input-group>
      </a-form-item>

      <a-form-item :label="t('system.job.misfirePolicy')" name="misfirePolicy">
        <DictSelect
          v-model:model-value="form.misfirePolicy"
          dict-type="sys_job_misfire_policy"
          :placeholder="t('system.job.misfirePolicyPlaceholder')"
        />
      </a-form-item>

      <a-form-item :label="t('system.job.concurrent')" name="concurrent">
        <DictSelect
          v-model:model-value="form.concurrent"
          dict-type="sys_job_concurrent"
          :placeholder="t('system.job.concurrentPlaceholder')"
        />
      </a-form-item>

      <a-form-item v-if="form.jobExecutor === 'webhook'" :label="t('system.job.webhookEnabled')" name="webhookEnabled">
        <DictSwitch
          v-model:model-value="form.webhookEnabled"
          dict-type="sys_data_option"
          @change="handleWebhookEnabledChange"
        />
      </a-form-item>

      <template v-if="form.jobExecutor === 'webhook' && form.webhookEnabled === '1'">
        <a-form-item :label="t('system.job.webhookUrl')" name="webhookUrl">
          <a-input
            v-model:value="form.webhookUrl"
            :placeholder="t('system.job.webhookUrlPlaceholder')"
            :maxlength="512"
          />
        </a-form-item>

        <a-form-item :label="t('system.job.webhookSecret')" name="webhookSecret">
          <a-input-password
            v-model:value="form.webhookSecret"
            :placeholder="t('system.job.webhookSecretPlaceholder')"
            :maxlength="128"
          />
        </a-form-item>
      </template>

      <a-form-item :label="t('common.status')" name="status">
        <DictSelect
          v-model:model-value="form.status"
          dict-type="sys_job_status"
          :placeholder="t('system.job.statusPlaceholder')"
        />
      </a-form-item>

      <!-- Webhook 触发 URL（仅编辑模式显示） -->
      <a-form-item v-if="isEdit" :label="t('system.job.webhookTriggerUrl')">
        <a-input :value="webhookTriggerUrl" readonly>
          <template #suffix>
            <a-button type="link" size="small" @click="copyWebhookUrl">
              <template #icon><CopyOutlined /></template>
            </a-button>
          </template>
        </a-input>
      </a-form-item>

      <a-form-item :label="t('common.remark')" name="remark">
        <a-textarea v-model:value="form.remark" :rows="3" :maxlength="500" show-count />
      </a-form-item>
    </a-form>

    <!-- Cron 表达式生成器弹窗 -->
    <CronGenerator v-model:visible="cronVisible" @confirm="handleCronConfirm" />
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import type { FormInstance } from 'ant-design-vue'
import { FieldTimeOutlined, CopyOutlined } from '@ant-design/icons-vue'
import { addJob, updateJob, getJobDetail } from '@/api/system/job.ts'
import type { JobCreateDTO, JobDetailVO } from '@/types/api/tool/job.ts'
import CronGenerator from './CronGenerator.vue'

const props = defineProps<{
  visible: boolean
  jobId?: number
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const { t } = useI18n()

const formRef = ref<FormInstance>()
const loading = ref(false)
const cronVisible = ref(false)
const jobDetail = ref<JobDetailVO | null>(null)

const isEdit = computed(() => props.jobId !== undefined)

// Webhook 触发 URL（只读）
const webhookTriggerUrl = computed(() => {
  if (isEdit.value && props.jobId) {
    return `${window.location.origin}/webhook/job/${props.jobId}`
  }
  return ''
})

const targetPlaceholder = computed(() => {
  if (form.jobExecutor === 'python') {
    return t('system.job.pythonTargetPlaceholder')
  } else if (form.jobExecutor === 'webhook') {
    return t('system.job.webhookTargetPlaceholder')
  }
  return ''
})

// 表单数据
const form = reactive<JobCreateDTO>({
  jobName: '',
  jobGroup: 'DEFAULT',
  jobExecutor: 'python',
  invokeTarget: '',
  jobArgs: undefined,
  jobKwargs: undefined,
  cronExpression: '',
  misfirePolicy: '1',
  concurrent: '0',
  webhookEnabled: '0',
  webhookUrl: undefined,
  webhookSecret: undefined,
  status: '0',
  remark: undefined,
})

// 表单验证规则
const rules = {
  jobName: [{ required: true, message: t('system.job.jobNameRequired') }],
  jobGroup: [{ required: true, message: t('system.job.jobGroupRequired') }],
  jobExecutor: [{ required: true, message: t('system.job.jobExecutorRequired') }],
  invokeTarget: [{ required: true, message: t('system.job.invokeTargetRequired') }],
  cronExpression: [{ required: true, message: t('system.job.cronExpressionRequired') }],
  misfirePolicy: [{ required: true, message: t('system.job.misfirePolicyRequired') }],
  concurrent: [{ required: true, message: t('system.job.concurrentRequired') }],
  webhookUrl: [
    {
      validator: (_rule: any, value: string) => {
        if (form.jobExecutor === 'webhook' && form.webhookEnabled === '1' && !value) {
          return Promise.reject(t('system.job.webhookUrlRequired'))
        }
        return Promise.resolve()
      },
    },
  ],
  status: [{ required: true, message: t('system.job.statusRequired') }],
}

// 执行器类型变化
const handleExecutorChange = () => {
  if (form.jobExecutor === 'python') {
    form.invokeTarget = 'graphedu.jobs.sample_task.sample_task'
  } else if (form.jobExecutor === 'webhook') {
    form.invokeTarget = 'graphedu.jobs.webhook_handler.webhook_entry'
  }
}

// Webhook 启用状态变化
const handleWebhookEnabledChange = () => {
  if (form.webhookEnabled === '0') {
    form.webhookUrl = undefined
    form.webhookSecret = undefined
  }
}

// Cron 表达式确认
const handleCronConfirm = (cron: string) => {
  form.cronExpression = cron
}

// 复制 Webhook URL
const copyWebhookUrl = async () => {
  if (!webhookTriggerUrl.value) return

  try {
    await navigator.clipboard.writeText(webhookTriggerUrl.value)
    message.success(t('system.job.webhookUrlCopied'))
  } catch {
    // 如果 clipboard API 不可用，使用传统方法
    const textarea = document.createElement('textarea')
    textarea.value = webhookTriggerUrl.value
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    try {
      document.execCommand('copy')
      message.success(t('system.job.webhookUrlCopied'))
    } catch {
      message.error(t('system.job.webhookUrlCopyFailed'))
    } finally {
      document.body.removeChild(textarea)
    }
  }
}

// 获取任务详情
const fetchJobDetail = async () => {
  if (!props.jobId) return

  loading.value = true
  try {
    const { data } = await getJobDetail(props.jobId)
    jobDetail.value = data
    Object.assign(form, {
      jobName: data.jobName,
      jobGroup: data.jobGroup as 'DEFAULT' | 'SYSTEM',
      jobExecutor: data.jobExecutor as 'python' | 'webhook',
      invokeTarget: data.invokeTarget,
      jobArgs: data.jobArgs,
      jobKwargs: data.jobKwargs,
      cronExpression: data.cronExpression,
      misfirePolicy: data.misfirePolicy as '1' | '2' | '3',
      concurrent: data.concurrent as '0' | '1',
      webhookEnabled: data.webhookEnabled as '0' | '1',
      webhookUrl: data.webhookUrl,
      webhookSecret: data.webhookSecret,
      status: data.status as '0' | '1',
      remark: data.remark,
    })
  } finally {
    loading.value = false
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    if (isEdit.value) {
      await updateJob({ ...form, jobId: props.jobId! })
      message.success(t('common.updateSuccess'))
    } else {
      await addJob(form)
      message.success(t('common.addSuccess'))
    }

    emit('update:visible', false)
    emit('success')
  } catch {
    // 验证失败或请求失败
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  emit('update:visible', false)
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(form, {
    jobName: '',
    jobGroup: 'DEFAULT',
    jobExecutor: 'python',
    invokeTarget: '',
    jobArgs: undefined,
    jobKwargs: undefined,
    cronExpression: '',
    misfirePolicy: '1',
    concurrent: '0',
    webhookEnabled: '0',
    webhookUrl: undefined,
    webhookSecret: undefined,
    status: '0',
    remark: undefined,
  })
}

// 监听弹窗显示状态
watch(
  () => props.visible,
  (val) => {
    if (val) {
      if (isEdit.value) {
        fetchJobDetail()
      } else {
        resetForm()
      }
    } else {
      resetForm()
    }
  }
)
</script>

<style scoped>
:deep(.ant-modal-body) {
  max-height: 60vh;
  overflow-y: auto;
}
</style>
