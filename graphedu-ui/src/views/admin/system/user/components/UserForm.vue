<template>
  <a-modal
    :open="visible"
    :title="title"
    :confirm-loading="loading"
    :width="700"
    @cancel="handleCancel"
    @ok="handleSubmit"
  >
    <a-spin :spinning="loading" :tip="t('common.loading')">
      <a-form ref="formRef" :model="form" :rules="rules as any" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-row>
          <a-col :span="24">
            <a-form-item :label="t('system.user.nickName')" name="nickName">
              <a-input
                v-model:value="form.nickName"
                :placeholder="t('system.user.nickNamePlaceholder')"
                :maxlength="30"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row>
          <a-col :span="24">
            <a-form-item :label="t('system.user.dept')" name="deptIds">
              <a-tree-select
                v-model:value="form.deptIds"
                :tree-data="deptTreeData"
                :field-names="{
                  label: 'deptName',
                  value: 'deptId',
                  children: 'children',
                }"
                :placeholder="t('system.user.deptPlaceholder')"
                tree-checkable
                allow-clear
                tree-default-expand-all
                multiple
                show-checked-strategy="SHOW_PARENT"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row>
          <a-col :span="24">
            <a-form-item :label="t('system.user.phonenumber')" name="phonenumber">
              <a-input
                v-model:value="form.phonenumber"
                :placeholder="t('system.user.phonenumberPlaceholder')"
                :maxlength="11"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row>
          <a-col :span="24">
            <a-form-item :label="t('common.email')" name="email">
              <a-input v-model:value="form.email" :placeholder="t('common.emailPlaceholder')" :maxlength="50" />
            </a-form-item>
          </a-col>
        </a-row>

        <template v-if="!isEdit">
          <a-row>
            <a-col :span="24">
              <a-form-item :label="t('common.userName')" name="userName">
                <a-input v-model:value="form.userName" :placeholder="t('common.userNamePlaceholder')" :maxlength="30" />
              </a-form-item>
            </a-col>
          </a-row>

          <a-row>
            <a-col :span="24">
              <a-form-item :label="t('system.user.password')" name="password">
                <a-input-password
                  v-model:value="form.password"
                  :placeholder="t('common.pleaseInput')"
                  :maxlength="20"
                />
              </a-form-item>
            </a-col>
          </a-row>
        </template>

        <a-row>
          <a-col :span="24">
            <a-form-item :label="t('system.user.userType')" name="userType">
              <DictSelect
                v-model:model-value="form.userType"
                dict-type="sys_user_type"
                :placeholder="t('system.user.userTypePlaceholder')"
                allow-clear
              />
            </a-form-item>
          </a-col>
        </a-row>

        <!-- 学生信息（内联创建/编辑，当 userType = 学生时显示） -->
        <template v-if="form.userType === 1">
          <a-divider orientation="left">学生信息</a-divider>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item
                label="真实姓名"
                name="studentRealName"
                :label-col="{ span: 12 }"
                :wrapper-col="{ span: 12 }"
              >
                <a-input v-model:value="form.studentRealName" placeholder="请输入真实姓名" :maxlength="64" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="学号" name="studentNo" :label-col="{ span: 12 }" :wrapper-col="{ span: 12 }">
                <a-input v-model:value="form.studentNo" placeholder="请输入学号" :maxlength="32" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="学院" :label-col="{ span: 12 }" :wrapper-col="{ span: 12 }">
                <a-input v-model:value="form.studentFaculty" placeholder="请输入学院" :maxlength="64" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="专业" :label-col="{ span: 12 }" :wrapper-col="{ span: 12 }">
                <a-input v-model:value="form.studentMajor" placeholder="请输入专业" :maxlength="64" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="年级" :label-col="{ span: 12 }" :wrapper-col="{ span: 12 }">
                <a-input v-model:value="form.studentGrade" placeholder="请输入年级" :maxlength="20" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="班级" :label-col="{ span: 12 }" :wrapper-col="{ span: 12 }">
                <a-input v-model:value="form.studentClassName" placeholder="请输入班级" :maxlength="64" />
              </a-form-item>
            </a-col>
          </a-row>
        </template>

        <!-- 教师信息（内联创建/编辑，当 userType = 教师时显示） -->
        <template v-if="form.userType === 2">
          <a-divider orientation="left">教师信息</a-divider>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item
                label="真实姓名"
                name="teacherRealName"
                :label-col="{ span: 12 }"
                :wrapper-col="{ span: 12 }"
              >
                <a-input v-model:value="form.teacherRealName" placeholder="请输入真实姓名" :maxlength="64" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="工号" name="teacherNo" :label-col="{ span: 12 }" :wrapper-col="{ span: 12 }">
                <a-input v-model:value="form.teacherNo" placeholder="请输入工号" :maxlength="32" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="学院" :label-col="{ span: 12 }" :wrapper-col="{ span: 12 }">
                <a-input v-model:value="form.teacherFaculty" placeholder="请输入学院" :maxlength="64" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="职称" :label-col="{ span: 12 }" :wrapper-col="{ span: 12 }">
                <a-input v-model:value="form.teacherTitle" placeholder="请输入职称" :maxlength="32" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="研究方向" :label-col="{ span: 12 }" :wrapper-col="{ span: 12 }">
                <a-input v-model:value="form.teacherResearchDirection" placeholder="请输入研究方向" :maxlength="255" />
              </a-form-item>
            </a-col>
          </a-row>
        </template>

        <a-row>
          <a-col :span="24">
            <a-form-item :label="t('common.status')" name="status">
              <DictRadio v-model:model-value="form.status" dict-type="sys_data_status" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row>
          <a-col :span="24">
            <a-form-item :label="t('system.user.role')" name="roleIds">
              <a-select
                v-model:value="form.roleIds"
                mode="multiple"
                :placeholder="t('system.user.rolePlaceholder')"
                allow-clear
                :options="roleOptions"
                :field-names="{ label: 'roleName', value: 'roleId' }"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row>
          <a-col :span="24">
            <a-form-item :label="t('common.remark')">
              <a-textarea
                v-model:value="form.remark"
                :placeholder="t('system.user.pleaseEnterContent')"
                :rows="3"
                :maxlength="200"
                show-count
              />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-spin>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import type { FormInstance } from 'ant-design-vue'
import { addUser, updateUser, getUserDetail } from '@/api/system/user.ts'
import { getRoleList } from '@/api/system/role.ts'
import type { UserCreateDTO, UserUpdateDTO } from '@/types/api/system/user.ts'
import type { DeptTreeVO } from '@/types/api/system/dept.ts'
import type { RoleListVO } from '@/types/api/system/role.ts'
import DictSelect from '../../../../../components/dict/DictSelect.vue'
import DictRadio from '../../../../../components/dict/DictRadio.vue'

const { t } = useI18n()

interface Props {
  visible: boolean
  userId?: number
  deptOptions: DeptTreeVO[]
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const loading = ref(false)
const roleOptions = ref<RoleListVO[]>([])

// 部门树数据转换
const deptTreeData = computed(() => {
  return props.deptOptions
})

// 是否编辑模式
const isEdit = computed(() => !!props.userId)

// 弹窗标题
const title = computed(() => (isEdit.value ? t('system.user.editUser') : t('system.user.addUser')))

// 表单数据
const form = reactive<Partial<UserCreateDTO & UserUpdateDTO>>({
  nickName: '',
  deptIds: [],
  phonenumber: '',
  email: '',
  userName: '',
  password: '',
  userType: undefined,
  status: '0',
  roleIds: [],
  remark: '',
  // 学生信息
  studentRealName: '',
  studentNo: '',
  studentFaculty: '',
  studentMajor: '',
  studentGrade: '',
  studentClassName: '',
  // 教师信息
  teacherRealName: '',
  teacherNo: '',
  teacherFaculty: '',
  teacherTitle: '',
  teacherResearchDirection: '',
})

// 表单验证规则
const rules: Record<string, any> = {
  nickName: [
    {
      required: true,
      message: t('system.user.nickNameRequired'),
      trigger: 'blur',
    },
  ],
  userName: [
    {
      required: true,
      message: t('system.user.userNameRequired'),
      trigger: 'blur',
    },
    {
      min: 2,
      max: 20,
      message: t('system.user.userNameLengthInvalid'),
      trigger: 'blur',
    },
  ],
  password: [
    {
      required: true,
      message: t('system.user.passwordRequired'),
      trigger: 'blur',
    },
    {
      min: 5,
      max: 20,
      message: t('system.user.passwordLengthInvalid'),
      trigger: 'blur',
    },
    {
      pattern: /^[^<>"'|\\]+$/,
      message: t('system.user.passwordInvalidChars'),
      trigger: 'blur',
    },
  ],
  email: [
    {
      type: 'email',
      message: t('system.user.emailFormatInvalid'),
      trigger: ['blur', 'change'],
    },
  ],
  phonenumber: [
    {
      pattern: /^1[3|4|5|6|7|8|9][0-9]\d{8}$/,
      message: t('system.user.phonenumberFormatInvalid'),
      trigger: 'blur',
    },
  ],
}

// 获取角色列表
const getRoles = async () => {
  try {
    const res = await getRoleList({ page: 1, size: 100 })
    if (res.code === 200) {
      roleOptions.value = (res.data.rows || []).filter((r) => r.status === '0')
    }
  } catch (_error) {
    message.error(t('common.getRoleListFailed'))
  }
}

// 获取用户详情（编辑模式）
const getUserInfo = async () => {
  if (!props.userId) return

  loading.value = true
  try {
    const res = await getUserDetail(props.userId)
    if (res.code === 200) {
      const user = res.data
      Object.assign(form, {
        nickName: user.nickName,
        deptIds: user.deptIds || [],
        phonenumber: user.phonenumber,
        email: user.email,
        userType: user.userType,
        status: user.status,
        roleIds: user.roleIds || [],
        remark: user.remark,
      })
      // 从已有的学生/教师信息填充内联字段
      if (user.student) {
        form.studentRealName = user.student.realName || ''
        form.studentNo = user.student.studentNo || ''
        form.studentFaculty = user.student.faculty || ''
        form.studentMajor = user.student.major || ''
        form.studentGrade = user.student.grade || ''
        form.studentClassName = user.student.className || ''
      }
      if (user.teacher) {
        form.teacherRealName = user.teacher.realName || ''
        form.teacherNo = user.teacher.teacherNo || ''
        form.teacherFaculty = user.teacher.faculty || ''
        form.teacherTitle = user.teacher.title || ''
        form.teacherResearchDirection = user.teacher.researchDirection || ''
      }
    }
  } catch (_error) {
    message.error(t('system.user.getUserInfoFailed'))
  } finally {
    loading.value = false
  }
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(form, {
    nickName: '',
    deptIds: [],
    phonenumber: '',
    email: '',
    userName: '',
    password: '',
    userType: undefined,
    status: '0',
    roleIds: [],
    remark: '',
    studentRealName: '',
    studentNo: '',
    studentFaculty: '',
    studentMajor: '',
    studentGrade: '',
    studentClassName: '',
    teacherRealName: '',
    teacherNo: '',
    teacherFaculty: '',
    teacherTitle: '',
    teacherResearchDirection: '',
  })
}

// 构建身份数据（仅在 userType 匹配时附加）
const buildIdentityData = (): Record<string, string | undefined> => {
  const data: Record<string, string | undefined> = {}
  if (form.userType === 1) {
    data.studentRealName = form.studentRealName || undefined
    data.studentNo = form.studentNo || undefined
    data.studentFaculty = form.studentFaculty || undefined
    data.studentMajor = form.studentMajor || undefined
    data.studentGrade = form.studentGrade || undefined
    data.studentClassName = form.studentClassName || undefined
  }
  if (form.userType === 2) {
    data.teacherRealName = form.teacherRealName || undefined
    data.teacherNo = form.teacherNo || undefined
    data.teacherFaculty = form.teacherFaculty || undefined
    data.teacherTitle = form.teacherTitle || undefined
    data.teacherResearchDirection = form.teacherResearchDirection || undefined
  }
  return data
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    const identityData = buildIdentityData()

    if (isEdit.value) {
      const data: UserUpdateDTO & { userType?: number } = {
        userId: props.userId!,
        nickName: form.nickName,
        deptIds: form.deptIds,
        phonenumber: form.phonenumber,
        email: form.email,
        userType: form.userType as number | undefined,
        status: form.status,
        roleIds: form.roleIds,
        remark: form.remark,
        ...identityData,
      }
      const res = await updateUser(data)
      if (res.code === 200) {
        message.success(t('common.updateSuccess'))
        emit('success')
      } else {
        message.error(res.msg || '操作失败')
      }
    } else {
      const data: UserCreateDTO = {
        userName: form.userName!,
        nickName: form.nickName!,
        password: form.password!,
        deptIds: form.deptIds,
        phonenumber: form.phonenumber,
        email: form.email,
        userType: form.userType as number | undefined,
        status: form.status,
        roleIds: form.roleIds,
        remark: form.remark,
        ...identityData,
      }
      const res = await addUser(data)
      if (res.code === 200) {
        message.success(t('common.addSuccess'))
        emit('success')
      } else {
        message.error(res.msg || '操作失败')
      }
    }
  } catch (error: any) {
    if (error.errorFields) {
      return
    }
    message.error(isEdit.value ? t('common.updateFailed') : t('common.addFailed'))
  } finally {
    loading.value = false
  }
}

// 用户类型切换时清空身份字段
watch(
  () => form.userType,
  (newType, oldType) => {
    if (!oldType || newType === oldType) return
    // 清空所有身份字段
    form.studentRealName = ''
    form.studentNo = ''
    form.studentFaculty = ''
    form.studentMajor = ''
    form.studentGrade = ''
    form.studentClassName = ''
    form.teacherRealName = ''
    form.teacherNo = ''
    form.teacherFaculty = ''
    form.teacherTitle = ''
    form.teacherResearchDirection = ''
  }
)

// 取消
const handleCancel = () => {
  emit('update:visible', false)
}

// 监听弹窗显示
watch(
  () => props.visible,
  (val) => {
    if (val) {
      getRoles()
      if (isEdit.value) {
        getUserInfo()
      }
    } else {
      resetForm()
    }
  }
)
</script>

<style scoped>
:deep(.ant-form-item) {
  margin-bottom: 16px;
}
</style>
