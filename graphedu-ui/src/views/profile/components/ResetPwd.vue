<template>
  <a-form ref="formRef" :model="form" :rules="rules as any" :label-col="{ span: 4 }" :wrapper-col="{ span: 16 }">
    <a-form-item label="旧密码" name="oldPassword">
      <a-input-password v-model:value="form.oldPassword" placeholder="请输入旧密码" />
    </a-form-item>
    <a-form-item label="新密码" name="newPassword">
      <a-input-password v-model:value="form.newPassword" placeholder="请输入新密码" />
    </a-form-item>
    <a-form-item label="确认密码" name="confirmPassword">
      <a-input-password v-model:value="form.confirmPassword" placeholder="请确认新密码" />
    </a-form-item>
    <a-form-item :wrapper-col="{ offset: 4 }">
      <a-space>
        <a-button type="primary" :loading="loading" @click="handleSubmit"> 保存 </a-button>
        <a-button @click="handleReset">重置</a-button>
      </a-space>
    </a-form-item>
  </a-form>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import type { FormInstance } from 'ant-design-vue'
import { updateUserPassword } from '@/api/system/user'

const formRef = ref<FormInstance>()
const loading = ref(false)

// 表单数据
const form = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

// 确认密码验证
const validateConfirmPassword = async (_rule: any, value: string) => {
  if (value !== form.newPassword) {
    return Promise.reject(new Error('两次输入的密码不一致'))
  }
  return Promise.resolve()
}

// 表单验证规则
const rules = {
  oldPassword: [{ required: true, message: '旧密码不能为空', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '新密码不能为空', trigger: 'blur' },
    { min: 6, max: 20, message: '长度在 6 到 20 个字符', trigger: 'blur' },
    {
      pattern: /^[^<>"'|\\]+$/,
      message: '不能包含非法字符：< > " \' \\ |',
      trigger: 'blur',
    },
  ],
  confirmPassword: [
    { required: true, message: '确认密码不能为空', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    const res = await updateUserPassword({
      old_password: form.oldPassword,
      new_password: form.newPassword,
    })
    if (res.code === 200) {
      message.success('修改成功')
      handleReset()
    }
  } catch (error: any) {
    if (error.errorFields) {
      // 表单验证失败
      return
    }
    message.error('修改失败')
  } finally {
    loading.value = false
  }
}

// 重置表单
const handleReset = () => {
  formRef.value?.resetFields()
  form.oldPassword = ''
  form.newPassword = ''
  form.confirmPassword = ''
}
</script>

<style scoped>
:deep(.ant-form-item) {
  margin-bottom: 20px;
}
</style>
