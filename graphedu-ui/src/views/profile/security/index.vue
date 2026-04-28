<template>
  <div class="account-security-page">
    <a-card :bordered="false" title="账号安全">
      <template #extra>
        <span class="security-tip">保护您的账号安全，建议定期更新密码和绑定信息</span>
      </template>

      <a-list item-layout="horizontal" :data-source="securityItems">
        <template #renderItem="{ item }">
          <a-list-item class="security-item">
            <a-list-item-meta>
              <template #avatar>
                <a-avatar :style="{ backgroundColor: item.color }" :size="44">
                  <component :is="item.icon" style="font-size: 22px" />
                </a-avatar>
              </template>
              <template #title>
                <span class="item-title">{{ item.title }}</span>
              </template>
              <template #description>
                <span :class="item.statusClass">
                  {{ item.statusText }}
                </span>
              </template>
            </a-list-item-meta>
            <template #actions>
              <a-button v-if="item.disabled" type="link" disabled>
                {{ item.actionText }}
              </a-button>
              <a-button v-else type="link" @click="item.action">
                {{ item.actionText }}
              </a-button>
            </template>
          </a-list-item>
        </template>
      </a-list>
    </a-card>

    <!-- 修改密码弹窗 -->
    <a-modal
      v-model:open="passwordModalVisible"
      title="修改密码"
      :width="modalWidth"
      :confirm-loading="passwordLoading"
      @ok="handlePasswordSubmit"
      @cancel="handlePasswordCancel"
    >
      <a-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules as any"
        :label-col="formLayout.labelCol"
        :wrapper-col="formLayout.wrapperCol"
        class="mt-4"
      >
        <a-form-item label="旧密码" name="oldPassword">
          <a-input-password v-model:value="passwordForm.oldPassword" placeholder="请输入旧密码" size="large">
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>
        <a-form-item label="新密码" name="newPassword">
          <a-input-password
            v-model:value="passwordForm.newPassword"
            placeholder="请输入新密码（6-20位，不能包含非法字符）"
            :maxlength="20"
            size="large"
          >
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>
        <a-form-item label="确认密码" name="confirmPassword">
          <a-input-password
            v-model:value="passwordForm.confirmPassword"
            placeholder="请再次输入新密码"
            :maxlength="20"
            size="large"
          >
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 修改手机号弹窗 -->
    <a-modal
      v-model:open="phoneModalVisible"
      title="修改手机号"
      :width="modalWidth"
      :confirm-loading="phoneLoading"
      @ok="handlePhoneSubmit"
      @cancel="handlePhoneCancel"
    >
      <a-form
        ref="phoneFormRef"
        :model="phoneForm"
        :rules="phoneRules as any"
        :label-col="formLayout.labelCol"
        :wrapper-col="formLayout.wrapperCol"
        class="mt-4"
      >
        <a-form-item label="当前手机号">
          <span class="current-value">{{ user.phonenumber ? maskPhone(user.phonenumber) : '未绑定' }}</span>
        </a-form-item>
        <a-form-item label="新手机号" name="phonenumber">
          <a-input v-model:value="phoneForm.phonenumber" placeholder="请输入新手机号" :maxlength="11" size="large">
            <template #prefix>
              <PhoneOutlined />
            </template>
          </a-input>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 修改邮箱弹窗 -->
    <a-modal
      v-model:open="emailModalVisible"
      title="修改邮箱"
      :width="modalWidth"
      :confirm-loading="emailLoading"
      @ok="handleEmailSubmit"
      @cancel="handleEmailCancel"
    >
      <a-form
        ref="emailFormRef"
        :model="emailForm"
        :rules="emailRules as any"
        :label-col="formLayout.labelCol"
        :wrapper-col="formLayout.wrapperCol"
        class="mt-4"
      >
        <a-form-item label="当前邮箱">
          <span class="current-value">{{ user.email ? maskEmail(user.email) : '未绑定' }}</span>
        </a-form-item>
        <a-form-item label="新邮箱" name="email">
          <a-input v-model:value="emailForm.email" placeholder="请输入新邮箱" :maxlength="50" size="large">
            <template #prefix>
              <MailOutlined />
            </template>
          </a-input>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { LockOutlined, PhoneOutlined, MailOutlined, WechatOutlined } from '@ant-design/icons-vue'
import { getUserProfile, updateUserProfile, updateUserPassword } from '@/api/system/user'
import type { UserProfileVO, UserDetailVO } from '@/types/api/system/user.ts'
import type { FormInstance } from 'ant-design-vue'
import { useBreakpoints } from '@/composables/useBreakpoints'

const { isMobile } = useBreakpoints()

const modalWidth = computed(() => (isMobile.value ? 'calc(100vw - 32px)' : 520))

const formLayout = computed(() =>
  isMobile.value
    ? { labelCol: { span: 24 }, wrapperCol: { span: 24 } }
    : { labelCol: { span: 6 }, wrapperCol: { span: 16 } }
)

// ============================================================================
// 用户数据
// ============================================================================

const userProfile = ref<UserProfileVO>({
  user: {} as UserDetailVO,
  roleKeys: [],
  roleNames: [],
  deptKeys: [],
  deptNames: [],
})

const user = computed(() => userProfile.value.user as UserDetailVO)

const getUserInfo = async () => {
  try {
    const res = await getUserProfile()
    if (res.code === 200) {
      userProfile.value = res.data
    }
  } catch {
    message.error('获取用户信息失败')
  }
}

// ============================================================================
// 敏感信息脱敏
// ============================================================================

function maskPhone(phone: string): string {
  if (!phone || phone.length < 7) return phone
  return phone.slice(0, 3) + '****' + phone.slice(-4)
}

function maskEmail(email: string): string {
  if (!email || !email.includes('@')) return email
  const [local = '', domain = ''] = email.split('@')
  const masked = local.length <= 1 ? local : local[0] + '***'
  return masked + '@' + domain
}

// ============================================================================
// 安全项列表
// ============================================================================

const securityItems = computed(() => [
  {
    title: '登录密码',
    icon: LockOutlined,
    color: '#1677ff',
    statusText: '已设置，建议定期更换密码以保障账号安全',
    statusClass: 'status-bound',
    actionText: '修改',
    disabled: false,
    action: () => {
      passwordModalVisible.value = true
    },
  },
  {
    title: '手机号',
    icon: PhoneOutlined,
    color: '#52c41a',
    statusText: user.value.phonenumber
      ? `已绑定：${maskPhone(user.value.phonenumber)}`
      : '未绑定，建议绑定手机号以提高账号安全性',
    statusClass: user.value.phonenumber ? 'status-bound' : 'status-unbound',
    actionText: user.value.phonenumber ? '修改' : '绑定',
    disabled: false,
    action: () => {
      phoneForm.phonenumber = ''
      phoneModalVisible.value = true
    },
  },
  {
    title: '邮箱',
    icon: MailOutlined,
    color: '#faad14',
    statusText: user.value.email ? `已绑定：${maskEmail(user.value.email)}` : '未绑定，建议绑定邮箱以便找回密码',
    statusClass: user.value.email ? 'status-bound' : 'status-unbound',
    actionText: user.value.email ? '修改' : '绑定',
    disabled: false,
    action: () => {
      emailForm.email = ''
      emailModalVisible.value = true
    },
  },
  {
    title: '微信',
    icon: WechatOutlined,
    color: '#07c160',
    statusText: '暂未开放微信绑定功能',
    statusClass: 'status-unbound',
    actionText: '绑定',
    disabled: true,
    action: () => {},
  },
])

// ============================================================================
// 修改密码
// ============================================================================

const passwordModalVisible = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref<FormInstance>()
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const validateConfirmPassword = async (_rule: any, value: string) => {
  if (value !== passwordForm.newPassword) {
    return Promise.reject(new Error('两次输入的密码不一致'))
  }
  return Promise.resolve()
}

const passwordRules = {
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

const handlePasswordSubmit = async () => {
  try {
    await passwordFormRef.value?.validate()
    passwordLoading.value = true

    const res = await updateUserPassword({
      old_password: passwordForm.oldPassword,
      new_password: passwordForm.newPassword,
    })
    if (res.code === 200) {
      message.success('密码修改成功，请重新登录')
      passwordModalVisible.value = false
      resetPasswordForm()
    }
  } catch (error: any) {
    if (error.errorFields) return
    message.error(error.msg || '密码修改失败')
  } finally {
    passwordLoading.value = false
  }
}

const handlePasswordCancel = () => {
  passwordModalVisible.value = false
  resetPasswordForm()
}

const resetPasswordForm = () => {
  passwordFormRef.value?.resetFields()
  passwordForm.oldPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
}

// ============================================================================
// 修改手机号
// ============================================================================

const phoneModalVisible = ref(false)
const phoneLoading = ref(false)
const phoneFormRef = ref<FormInstance>()
const phoneForm = reactive({
  phonenumber: '',
})

const phoneRules = {
  phonenumber: [
    { required: true, message: '手机号不能为空', trigger: 'blur' },
    {
      pattern: /^1[3-9]\d{9}$/,
      message: '请输入正确的手机号码',
      trigger: 'blur',
    },
  ],
}

const handlePhoneSubmit = async () => {
  try {
    await phoneFormRef.value?.validate()
    phoneLoading.value = true

    const res = await updateUserProfile({ phonenumber: phoneForm.phonenumber })
    if (res.code === 200) {
      message.success('手机号修改成功')
      phoneModalVisible.value = false
      phoneForm.phonenumber = ''
      await getUserInfo()
    }
  } catch (error: any) {
    if (error.errorFields) return
    message.error(error.msg || '手机号修改失败')
  } finally {
    phoneLoading.value = false
  }
}

const handlePhoneCancel = () => {
  phoneModalVisible.value = false
  phoneFormRef.value?.resetFields()
}

// ============================================================================
// 修改邮箱
// ============================================================================

const emailModalVisible = ref(false)
const emailLoading = ref(false)
const emailFormRef = ref<FormInstance>()
const emailForm = reactive({
  email: '',
})

const emailRules = {
  email: [
    { required: true, message: '邮箱不能为空', trigger: 'blur' },
    {
      type: 'email',
      message: '请输入正确的邮箱地址',
      trigger: ['blur', 'change'],
    },
  ],
}

const handleEmailSubmit = async () => {
  try {
    await emailFormRef.value?.validate()
    emailLoading.value = true

    const res = await updateUserProfile({ email: emailForm.email })
    if (res.code === 200) {
      message.success('邮箱修改成功')
      emailModalVisible.value = false
      emailForm.email = ''
      await getUserInfo()
    }
  } catch (error: any) {
    if (error.errorFields) return
    message.error(error.msg || '邮箱修改失败')
  } finally {
    emailLoading.value = false
  }
}

const handleEmailCancel = () => {
  emailModalVisible.value = false
  emailFormRef.value?.resetFields()
}

// ============================================================================
// 初始化
// ============================================================================

onMounted(() => {
  getUserInfo()
})
</script>

<style scoped>
.account-security-page {
  .security-tip {
    font-size: 13px;
    color: var(--ge-text-tertiary);
  }

  .security-item {
    padding: 16px 0;

    :deep(.ant-list-item-meta-avatar) {
      margin-top: 4px;
    }

    :deep(.ant-list-item-action) {
      margin-left: 16px;
    }

    .item-title {
      font-size: 15px;
      font-weight: 500;
      color: var(--ge-text-primary);
    }

    .status-bound {
      color: var(--ge-text-secondary);
      font-size: 13px;
    }

    .status-unbound {
      color: var(--ge-text-tertiary);
      font-size: 13px;
    }
  }

  .current-value {
    color: var(--ge-text-secondary);
  }

  .mt-4 {
    margin-top: 16px;
  }

  :deep(.ant-input-affix-wrapper) {
    border-radius: 6px;

    &:hover,
    &:focus,
    &.ant-input-affix-wrapper-focused {
      border-color: var(--ge-primary);
      box-shadow: 0 0 0 2px color-mix(in srgb, var(--ge-primary) 10%, transparent);
    }
  }
}
</style>
