<template>
  <a-form ref="formRef" :model="form" :rules="rules as any" :label-col="{ span: 4 }" :wrapper-col="{ span: 16 }">
    <a-form-item label="用户昵称" name="nickName">
      <a-input v-model:value="form.nickName" placeholder="请输入用户昵称" :maxlength="30" />
    </a-form-item>
    <a-form-item label="手机号码" name="phonenumber">
      <a-input v-model:value="form.phonenumber" placeholder="请输入手机号码" :maxlength="11" />
    </a-form-item>
    <a-form-item label="邮箱" name="email">
      <a-input v-model:value="form.email" placeholder="请输入邮箱" :maxlength="50" />
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
import { ref, reactive, watch } from 'vue'
import { message } from 'ant-design-vue'
import type { FormInstance } from 'ant-design-vue'
import { updateUserProfile } from '@/api/system/user'
import type { UserProfileUpdateDTO } from '@/types/api/system/user.ts'

interface Props {
  user: any
}

interface Emits {
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const loading = ref(false)

// 表单数据
const form = reactive<UserProfileUpdateDTO>({
  nickName: '',
  phonenumber: '',
  email: '',
  remark: '',
})

// 表单验证规则
const rules = {
  nickName: [{ required: true, message: '用户昵称不能为空', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] }],
  phonenumber: [{ pattern: /^1[3|4|5|6|7|8|9][0-9]\d{8}$/, message: '请输入正确的手机号码', trigger: 'blur' }],
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    const res = await updateUserProfile(form)
    if (res.code === 200) {
      message.success('修改成功')
      emit('success')
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
}

// 监听用户信息变化
watch(
  () => props.user,
  (user) => {
    if (user && user.userId) {
      form.nickName = user.nickName
      form.phonenumber = user.phonenumber
      form.email = user.email
      form.remark = user.remark
    }
  },
  { immediate: true }
)
</script>

<style scoped>
:deep(.ant-form-item) {
  margin-bottom: 20px;
}
</style>
