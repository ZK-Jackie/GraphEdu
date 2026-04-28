<template>
  <div class="profile-info-page">
    <!-- 头部卡片 - 头像和基本信息 -->
    <a-card :bordered="false" class="header-card">
      <a-row :gutter="24" align="middle">
        <!-- 头像区域 -->
        <a-col :xs="24" :md="8" :lg="6" class="avatar-col">
          <div class="avatar-section">
            <div class="avatar-wrapper">
              <a-avatar :size="avatarSize" :src="avatarUrl" class="user-avatar">
                <template #icon>
                  <UserOutlined />
                </template>
              </a-avatar>
            </div>
            <div class="avatar-actions">
              <a-upload :before-upload="beforeUpload" :show-upload-list="false" accept="image/*">
                <a-button type="primary" size="small" :loading="uploading">
                  <template #icon>
                    <UploadOutlined />
                  </template>
                  更换头像
                </a-button>
              </a-upload>
            </div>
          </div>
        </a-col>

        <!-- 基本信息预览 -->
        <a-col :xs="24" :md="16" :lg="18">
          <div class="user-summary">
            <h2 class="user-name">{{ user.nickName || '未设置昵称' }}</h2>
            <p class="user-account">@{{ user.userName || '未设置用户名' }}</p>
            <a-space class="user-tags" :size="8" wrap>
              <a-tag color="green">
                <template #icon>
                  <CheckCircleOutlined />
                </template>
                已认证
              </a-tag>
            </a-space>
          </div>
        </a-col>
      </a-row>
    </a-card>

    <!-- 详细信息卡片 -->
    <a-card :bordered="false" class="detail-card" title="详细信息">
      <template #extra>
        <a-button type="link" @click="toggleEdit">
          {{ isEditing ? '取消编辑' : '编辑资料' }}
          <template #icon>
            <EditOutlined v-if="!isEditing" />
            <CloseOutlined v-else />
          </template>
        </a-button>
      </template>

      <!-- 展示模式 -->
      <div v-if="!isEditing" class="info-display">
        <a-descriptions :column="responsiveColumn" bordered size="middle">
          <a-descriptions-item label="用户昵称">
            <span class="info-value">
              <UserOutlined class="info-icon" />
              {{ user.nickName || '未设置' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="用户名称">
            <span class="info-value">
              <IdcardOutlined class="info-icon" />
              {{ user.userName || '未设置' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="手机号码">
            <span class="info-value">
              <PhoneOutlined class="info-icon" />
              {{ user.phonenumber || '未绑定' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="邮箱">
            <span class="info-value">
              <MailOutlined class="info-icon" />
              {{ user.email || '未绑定' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="所属部门">
            <span class="info-value">
              <ApartmentOutlined class="info-icon" />
              {{ deptNames || '未分配' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="所属角色">
            <span class="info-value">
              <TeamOutlined class="info-icon" />
              {{ roleNames || '未分配' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="创建时间" :span="responsiveColumn">
            <span class="info-value">
              <ClockCircleOutlined class="info-icon" />
              {{ formatTime(user.createTime) }}
            </span>
          </a-descriptions-item>
        </a-descriptions>
      </div>

      <!-- 编辑模式 -->
      <div v-else class="info-edit">
        <a-form
          ref="formRef"
          :model="form"
          :rules="rules as any"
          :label-col="formLayout.labelCol"
          :wrapper-col="formLayout.wrapperCol"
        >
          <a-form-item label="用户昵称" name="nickName">
            <a-input v-model:value="form.nickName" placeholder="请输入用户昵称" :maxlength="30" size="large">
              <template #prefix>
                <UserOutlined />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item label="手机号码" name="phonenumber">
            <a-input v-model:value="form.phonenumber" placeholder="请输入手机号码" :maxlength="11" size="large">
              <template #prefix>
                <PhoneOutlined />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item label="邮箱" name="email">
            <a-input v-model:value="form.email" placeholder="请输入邮箱" :maxlength="50" size="large">
              <template #prefix>
                <MailOutlined />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item v-bind="submitLayout">
            <a-space :size="12">
              <a-button type="primary" :loading="loading" size="large" @click="handleSubmit">
                <template #icon>
                  <SaveOutlined />
                </template>
                保存修改
              </a-button>
              <a-button size="large" @click="handleCancel">
                <template #icon>
                  <CloseOutlined />
                </template>
                取消
              </a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </div>
    </a-card>

    <!-- 学生信息卡片 -->
    <a-card v-if="userStore.studentInfo" :bordered="false" class="education-card" title="教育信息">
      <template #extra>
        <a-button v-if="!editingStudent" type="link" @click="toggleEditStudent">
          <template #icon>
            <EditOutlined />
          </template>
          编辑
        </a-button>
      </template>

      <!-- 展示模式 -->
      <div v-if="!editingStudent">
        <a-descriptions :column="responsiveColumn" bordered size="middle">
          <a-descriptions-item label="真实姓名">
            <span class="info-value">
              <UserOutlined class="info-icon" />
              {{ userStore.studentInfo.realName || '未设置' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="学号">
            <span class="info-value">
              <IdcardOutlined class="info-icon" />
              {{ userStore.studentInfo.studentNo || '未设置' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="学院">
            <span class="info-value">
              <ApartmentOutlined class="info-icon" />
              {{ userStore.studentInfo.faculty || '未设置' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="专业">
            <span class="info-value">
              <BranchesOutlined class="info-icon" />
              {{ userStore.studentInfo.major || '未设置' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="年级">
            <span class="info-value">
              <CalendarOutlined class="info-icon" />
              {{ userStore.studentInfo.grade || '未设置' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="班级">
            <span class="info-value">
              <TeamOutlined class="info-icon" />
              {{ userStore.studentInfo.className || '未设置' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="性别">
            <span class="info-value">
              <ManOutlined v-if="userStore.studentInfo.gender === 1" class="info-icon" />
              <WomanOutlined v-else-if="userStore.studentInfo.gender === 2" class="info-icon" />
              <UserOutlined v-else class="info-icon" />
              {{ userStore.studentInfo.gender === 1 ? '男' : userStore.studentInfo.gender === 2 ? '女' : '未知' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="年龄">
            <span class="info-value">
              <ClockCircleOutlined class="info-icon" />
              {{ userStore.studentInfo.age || '未设置' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="自我介绍" :span="responsiveColumn">
            <span class="info-value">
              <FileTextOutlined class="info-icon" />
              {{ userStore.studentInfo.description || '未填写' }}
            </span>
          </a-descriptions-item>
        </a-descriptions>
      </div>

      <!-- 编辑模式 -->
      <div v-else class="info-edit">
        <a-form
          ref="studentFormRef"
          :model="studentForm"
          :rules="studentRules as any"
          :label-col="formLayout.labelCol"
          :wrapper-col="formLayout.wrapperCol"
        >
          <a-form-item label="真实姓名" name="realName">
            <a-input v-model:value="studentForm.realName" placeholder="请输入真实姓名" :maxlength="50" size="large">
              <template #prefix>
                <UserOutlined />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item label="学号" name="studentNo">
            <a-input v-model:value="studentForm.studentNo" placeholder="请输入学号" :maxlength="30" size="large">
              <template #prefix>
                <IdcardOutlined />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item label="学院" name="faculty">
            <a-input v-model:value="studentForm.faculty" placeholder="请输入学院" :maxlength="50" size="large">
              <template #prefix>
                <ApartmentOutlined />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item label="专业" name="major">
            <a-input v-model:value="studentForm.major" placeholder="请输入专业" :maxlength="50" size="large">
              <template #prefix>
                <BranchesOutlined />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item label="年级" name="grade">
            <a-input
              v-model:value="studentForm.grade"
              placeholder="请输入年级（如：2023）"
              :maxlength="10"
              size="large"
            >
              <template #prefix>
                <CalendarOutlined />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item label="班级" name="className">
            <a-input v-model:value="studentForm.className" placeholder="请输入班级" :maxlength="50" size="large">
              <template #prefix>
                <TeamOutlined />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item label="性别" name="gender">
            <a-select v-model:value="studentForm.gender" placeholder="请选择性别" size="large" :options="genderOptions" />
          </a-form-item>
          <a-form-item label="年龄" name="age">
            <a-input-number
              v-model:value="studentForm.age"
              placeholder="请输入年龄"
              :min="1"
              :max="150"
              size="large"
              class="w-full"
            >
              <template #prefix>
                <ClockCircleOutlined />
              </template>
            </a-input-number>
          </a-form-item>
          <a-form-item label="自我介绍" name="description">
            <a-textarea
              v-model:value="studentForm.description"
              placeholder="请输入自我介绍"
              :maxlength="500"
              :rows="4"
              show-count
            />
          </a-form-item>
          <a-form-item v-bind="submitLayout">
            <a-space :size="12">
              <a-button type="primary" :loading="studentLoading" size="large" @click="handleStudentSubmit">
                <template #icon>
                  <SaveOutlined />
                </template>
                保存修改
              </a-button>
              <a-button size="large" @click="handleStudentCancel">
                <template #icon>
                  <CloseOutlined />
                </template>
                取消
              </a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </div>
    </a-card>

    <!-- 教师信息卡片 -->
    <a-card v-if="userStore.teacherInfo" :bordered="false" class="education-card" title="教育信息">
      <template #extra>
        <a-button v-if="!editingTeacher" type="link" @click="toggleEditTeacher">
          <template #icon>
            <EditOutlined />
          </template>
          编辑
        </a-button>
      </template>

      <!-- 展示模式 -->
      <div v-if="!editingTeacher">
        <a-descriptions :column="responsiveColumn" bordered size="middle">
          <a-descriptions-item label="真实姓名">
            <span class="info-value">
              <UserOutlined class="info-icon" />
              {{ userStore.teacherInfo.realName || '未设置' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="工号">
            <span class="info-value">
              <IdcardOutlined class="info-icon" />
              {{ userStore.teacherInfo.teacherNo || '未设置' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="所属学院">
            <span class="info-value">
              <ApartmentOutlined class="info-icon" />
              {{ userStore.teacherInfo.faculty || '未设置' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="职称">
            <span class="info-value">
              <TrophyOutlined class="info-icon" />
              {{ userStore.teacherInfo.title || '未设置' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="研究方向" :span="responsiveColumn">
            <span class="info-value">
              <ExperimentOutlined class="info-icon" />
              {{ userStore.teacherInfo.researchDirection || '未设置' }}
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="个人简介" :span="responsiveColumn">
            <span class="info-value">
              <FileTextOutlined class="info-icon" />
              {{ userStore.teacherInfo.description || '未填写' }}
            </span>
          </a-descriptions-item>
        </a-descriptions>
      </div>

      <!-- 编辑模式 -->
      <div v-else class="info-edit">
        <a-form
          ref="teacherFormRef"
          :model="teacherForm"
          :rules="teacherRules as any"
          :label-col="formLayout.labelCol"
          :wrapper-col="formLayout.wrapperCol"
        >
          <a-form-item label="真实姓名" name="realName">
            <a-input v-model:value="teacherForm.realName" placeholder="请输入真实姓名" :maxlength="50" size="large">
              <template #prefix>
                <UserOutlined />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item label="工号" name="teacherNo">
            <a-input v-model:value="teacherForm.teacherNo" placeholder="请输入工号" :maxlength="30" size="large">
              <template #prefix>
                <IdcardOutlined />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item label="所属学院" name="faculty">
            <a-input v-model:value="teacherForm.faculty" placeholder="请输入所属学院" :maxlength="50" size="large">
              <template #prefix>
                <ApartmentOutlined />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item label="职称" name="title">
            <a-select
              v-model:value="teacherForm.title"
              placeholder="请选择职称"
              size="large"
              :options="[
                { label: '教授', value: '教授' },
                { label: '副教授', value: '副教授' },
                { label: '讲师', value: '讲师' },
                { label: '助教', value: '助教' },
              ]"
            />
          </a-form-item>
          <a-form-item label="研究方向" name="researchDirection">
            <a-input
              v-model:value="teacherForm.researchDirection"
              placeholder="请输入研究方向"
              :maxlength="100"
              size="large"
            >
              <template #prefix>
                <ExperimentOutlined />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item label="个人简介" name="description">
            <a-textarea
              v-model:value="teacherForm.description"
              placeholder="请输入个人简介"
              :maxlength="500"
              :rows="4"
              show-count
            />
          </a-form-item>
          <a-form-item v-bind="submitLayout">
            <a-space :size="12">
              <a-button type="primary" :loading="teacherLoading" size="large" @click="handleTeacherSubmit">
                <template #icon>
                  <SaveOutlined />
                </template>
                保存修改
              </a-button>
              <a-button size="large" @click="handleTeacherCancel">
                <template #icon>
                  <CloseOutlined />
                </template>
                取消
              </a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </div>
    </a-card>

    <!-- 图片裁剪弹窗 -->
    <a-modal v-model:open="cropVisible" title="裁剪头像" :width="modalWidth" @ok="handleCropConfirm">
      <div class="crop-container">
        <img ref="cropImage" :src="cropImageUrl" style="max-width: 100%" />
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useBreakpoints } from '@/composables/useBreakpoints'
import { message } from 'ant-design-vue'
import {
  UserOutlined,
  UploadOutlined,
  CheckCircleOutlined,
  EditOutlined,
  CloseOutlined,
  IdcardOutlined,
  PhoneOutlined,
  MailOutlined,
  ApartmentOutlined,
  TeamOutlined,
  ClockCircleOutlined,
  SaveOutlined,
  ManOutlined,
  WomanOutlined,
  BranchesOutlined,
  CalendarOutlined,
  FileTextOutlined,
  TrophyOutlined,
  ExperimentOutlined,
} from '@ant-design/icons-vue'
import { getUserProfile, updateUserProfile, updateUserAvatar } from '@/api/system/user'
import { uploadAvatar } from '@/api/system/upload'
import { updateStudent } from '@/api/education/student'
import { updateTeacher } from '@/api/education/teacher'
import type { UserProfileVO, UserDetailVO, UserProfileUpdateDTO } from '@/types/api/system/user.ts'
import type { FormInstance } from 'ant-design-vue'
import useUserStore from '@/stores/modules/user'
import type { StudentUpdateDTO } from '@/types/api/education/student.ts'
import type { TeacherUpdateDTO } from '@/types/api/education/teacher.ts'
import { parseTime } from '@/utils/common.ts'

// 用户 Store
const userStore = useUserStore()
const { isMobile } = useBreakpoints()

const avatarSize = computed(() => (isMobile.value ? 80 : 100))

const formLayout = computed(() =>
  isMobile.value
    ? { labelCol: { span: 24 }, wrapperCol: { span: 24 } }
    : { labelCol: { span: 4 }, wrapperCol: { span: 16 } }
)

const submitLayout = computed(() => (isMobile.value ? { wrapperCol: { span: 24 } } : { wrapperCol: { offset: 4 } }))

// 数据
const userProfile = ref<UserProfileVO>({
  user: {} as UserDetailVO,
  roleKeys: [],
  roleNames: [],
  deptKeys: [],
  deptNames: [],
})

// 用户信息
const user = computed(() => userProfile.value.user as UserDetailVO)

// ============================================================================
// 教育信息相关 - 学生信息
// ============================================================================

const editingStudent = ref(false)
const studentFormRef = ref<FormInstance>()
const studentLoading = ref(false)
const studentForm = reactive<StudentUpdateDTO>({
  studentId: 0,
  realName: '',
  studentNo: '',
  faculty: '',
  major: '',
  grade: '',
  className: '',
  gender: undefined,
  age: undefined,
  description: '',
})

// 学生表单验证规则
const studentRules = {
  realName: [{ required: true, message: '真实姓名不能为空', trigger: 'blur' }],
}

// 切换学生信息编辑状态
const toggleEditStudent = () => {
  if (!editingStudent.value && userStore.studentInfo) {
    // 进入编辑模式，初始化表单数据
    const info = userStore.studentInfo
    studentForm.studentId = info.studentId
    studentForm.realName = info.realName
    studentForm.studentNo = info.studentNo || ''
    studentForm.faculty = info.faculty || ''
    studentForm.major = info.major || ''
    studentForm.grade = info.grade || ''
    studentForm.className = info.className || ''
    studentForm.gender = info.gender ? (String(info.gender) as any) : undefined
    studentForm.age = info.age
    studentForm.description = info.description || ''
  }
  editingStudent.value = !editingStudent.value
}

// 取消学生信息编辑
const handleStudentCancel = () => {
  editingStudent.value = false
  studentFormRef.value?.resetFields()
}

// 提交学生信息修改
const handleStudentSubmit = async () => {
  try {
    await studentFormRef.value?.validate()
    studentLoading.value = true

    const res = await updateStudent(studentForm)
    if (res.code === 200) {
      message.success('学生信息修改成功')
      editingStudent.value = false
      // 重新获取用户信息以更新 store
      await userStore.fetchUserInfo()
      // 同时更新当前页面的用户信息
      await getUserInfo()
    }
  } catch (error: any) {
    if (error.errorFields) {
      return
    }
    message.error(error.msg || '学生信息修改失败')
  } finally {
    studentLoading.value = false
  }
}

// ============================================================================
// 教育信息相关 - 教师信息
// ============================================================================

const editingTeacher = ref(false)
const teacherFormRef = ref<FormInstance>()
const teacherLoading = ref(false)
const teacherForm = reactive<TeacherUpdateDTO>({
  teacherId: 0,
  realName: '',
  teacherNo: '',
  faculty: '',
  title: '',
  researchDirection: '',
  description: '',
})

// 教师表单验证规则
const teacherRules = {
  realName: [{ required: true, message: '真实姓名不能为空', trigger: 'blur' }],
}

// 切换教师信息编辑状态
const toggleEditTeacher = () => {
  if (!editingTeacher.value && userStore.teacherInfo) {
    // 进入编辑模式，初始化表单数据
    const info = userStore.teacherInfo
    teacherForm.teacherId = info.teacherId
    teacherForm.realName = info.realName
    teacherForm.teacherNo = info.teacherNo || ''
    teacherForm.faculty = info.faculty || ''
    teacherForm.title = info.title || ''
    teacherForm.researchDirection = info.researchDirection || ''
    teacherForm.description = info.description || ''
  }
  editingTeacher.value = !editingTeacher.value
}

// 取消教师信息编辑
const handleTeacherCancel = () => {
  editingTeacher.value = false
  teacherFormRef.value?.resetFields()
}

// 提交教师信息修改
const handleTeacherSubmit = async () => {
  try {
    await teacherFormRef.value?.validate()
    teacherLoading.value = true

    const res = await updateTeacher(teacherForm)
    if (res.code === 200) {
      message.success('教师信息修改成功')
      editingTeacher.value = false
      // 重新获取用户信息以更新 store
      await userStore.fetchUserInfo()
      // 同时更新当前页面的用户信息
      await getUserInfo()
    }
  } catch (error: any) {
    if (error.errorFields) {
      return
    }
    message.error(error.msg || '教师信息修改失败')
  } finally {
    teacherLoading.value = false
  }
}

// 性别选项
const genderOptions = [
  { label: '男', value: '1' },
  { label: '女', value: '2' },
  { label: '未知', value: '0' },
  { label: '其他', value: '9' },
]

// 部门名称
const deptNames = computed(() => {
  const names = userProfile.value.deptNames
  return names && names.length > 0 ? names.join('、') : '未分配'
})

// 角色名称
const roleNames = computed(() => {
  const names = userProfile.value.roleNames
  return names && names.length > 0 ? names.join('、') : '未分配'
})

// 编辑状态
const isEditing = ref(false)

// 表单
const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive<UserProfileUpdateDTO>({
  nickName: '',
  phonenumber: '',
  email: '',
  remark: '',
})

// 表单验证规则
const rules = {
  nickName: [{ required: true, message: '用户昵称不能为空', trigger: 'blur' }],
  email: [
    {
      type: 'email',
      message: '请输入正确的邮箱地址',
      trigger: ['blur', 'change'],
    },
  ],
  phonenumber: [
    {
      pattern: /^1[3|4|5|6|7|8|9][0-9]\d{8}$/,
      message: '请输入正确的手机号码',
      trigger: 'blur',
    },
  ],
}

// 头像上传
const cropVisible = ref(false)
const cropImageUrl = ref('')
const cropImage = ref<HTMLImageElement>()
const uploading = ref(false)
const uploadedFilePath = ref('')

// 头像 URL
const avatarUrl = computed(() => {
  if (uploadedFilePath.value) {
    return uploadedFilePath.value
  }
  if (user.value.avatarPath) {
    return user.value.avatarPath
  }
  return undefined
})

// 响应式列数
const responsiveColumn = computed(() => (isMobile.value ? 1 : 2))

const modalWidth = computed(() => (isMobile.value ? 'calc(100vw - 32px)' : 600))

// 切换编辑状态
const toggleEdit = () => {
  if (!isEditing.value) {
    // 进入编辑模式，初始化表单数据
    form.nickName = user.value.nickName || ''
    form.phonenumber = user.value.phonenumber || ''
    form.email = user.value.email || ''
    form.remark = user.value.remark || ''
  }
  isEditing.value = !isEditing.value
}

// 取消编辑
const handleCancel = () => {
  isEditing.value = false
  formRef.value?.resetFields()
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true

    const res = await updateUserProfile(form)
    if (res.code === 200) {
      message.success('修改成功')
      isEditing.value = false
      await getUserInfo()
    }
  } catch (error: any) {
    if (error.errorFields) {
      return
    }
    message.error('修改失败')
  } finally {
    loading.value = false
  }
}

// 获取用户信息
const getUserInfo = async () => {
  try {
    const res = await getUserProfile()
    if (res.code === 200) {
      userProfile.value = res.data
    }
  } catch (error) {
    message.error('获取用户信息失败')
  }
}

// 格式化时间
const formatTime = (time: string | undefined) => {
  if (!time) return '未设置'
  return parseTime(time)
}

// 上传前校验
const beforeUpload = (file: File) => {
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    message.error('只能上传图片文件')
    return false
  }

  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isLt2M) {
    message.error('图片大小不能超过 2MB')
    return false
  }

  const reader = new FileReader()
  reader.onload = (e) => {
    cropImageUrl.value = e.target?.result as string
    cropVisible.value = true
  }
  reader.readAsDataURL(file)

  return false
}

// 确认裁剪并上传
const handleCropConfirm = async () => {
  try {
    uploading.value = true

    const res = await fetch(cropImageUrl.value)
    const blob = await res.blob()
    const file = new File([blob], 'avatar.jpg', { type: 'image/jpeg' })

    const uploadRes = await uploadAvatar(file)
    if (uploadRes.code === 200 && uploadRes.data) {
      const updateRes = await updateUserAvatar(uploadRes.data.fileId)
      if (updateRes.code === 200) {
        message.success('头像上传成功')
        uploadedFilePath.value = uploadRes.data.filePath
        cropVisible.value = false
        await getUserInfo()
      }
    }
  } catch (error: any) {
    console.error('头像上传失败:', error)
    message.error(error.message || '头像上传失败')
  } finally {
    uploading.value = false
  }
}

// 监听 avatarFileId 变化
watch(
  () => user.value.avatarFileId,
  () => {
    uploadedFilePath.value = ''
  }
)

onMounted(() => {
  getUserInfo()
})
</script>

<style scoped>
.profile-info-page {
  .header-card {
    margin-bottom: 16px;
    background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
    color: white;

    :deep(.ant-card-body) {
      padding: 32px;
    }

    .avatar-col {
      text-align: center;
      margin-bottom: 16px;

      @media (min-width: 768px) {
        margin-bottom: 0;
        text-align: left;
      }
    }

    .avatar-section {
      display: inline-block;

      .avatar-wrapper {
        position: relative;
        display: inline-block;

        .user-avatar {
          border: 4px solid rgba(255, 255, 255, 0.3);
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
          background: rgba(255, 255, 255, 0.1);
          color: white;

          :deep(.anticon) {
            color: white;
            font-size: 48px;
          }
        }
      }

      .avatar-actions {
        margin-top: 16px;
      }
    }

    .user-summary {
      @media (max-width: 767px) {
        text-align: center;
        margin-top: 16px;
      }

      .user-name {
        color: white;
        font-size: 28px;
        font-weight: 600;
        margin-bottom: 8px;

        @media (max-width: 767px) {
          font-size: 24px;
        }
      }

      .user-account {
        color: rgba(255, 255, 255, 0.85);
        font-size: 16px;
        margin-bottom: 16px;
      }

      .user-tags {
        :deep(.ant-tag) {
          background: rgba(255, 255, 255, 0.2);
          border-color: rgba(255, 255, 255, 0.3);
          color: white;

          .anticon {
            color: white;
          }
        }
      }
    }
  }

  .detail-card {
    :deep(.ant-descriptions) {
      .ant-descriptions-item-label {
        background: var(--ge-bg-elevated);
        font-weight: 500;
        width: 140px;
      }

      .ant-descriptions-item-content {
        background: var(--ge-bg-container);
      }
    }

    @media (max-width: 767px) {
      :deep(.ant-descriptions) {
        .ant-descriptions-item-label {
          width: auto;
          min-width: 80px;
        }
      }
    }

    .info-display {
      .info-value {
        display: inline-flex;
        align-items: center;
        gap: 8px;

        .info-icon {
          color: var(--ge-primary);
          font-size: 16px;
        }
      }
    }

    .info-edit {
      :deep(.ant-form-item) {
        margin-bottom: 24px;
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
  }

  .education-card {
    margin-top: 16px;

    :deep(.ant-descriptions) {
      .ant-descriptions-item-label {
        background: var(--ge-bg-elevated);
        font-weight: 500;
        width: 140px;
      }

      .ant-descriptions-item-content {
        background: var(--ge-bg-container);
      }
    }

    @media (max-width: 767px) {
      :deep(.ant-descriptions) {
        .ant-descriptions-item-label {
          width: auto;
          min-width: 80px;
        }
      }
    }

    .info-display {
      .info-value {
        display: inline-flex;
        align-items: center;
        gap: 8px;

        .info-icon {
          color: var(--ge-primary);
          font-size: 16px;
        }
      }
    }

    .info-edit {
      :deep(.ant-form-item) {
        margin-bottom: 24px;
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

      :deep(.ant-input-number) {
        width: 100%;

        .ant-input-number-input {
          border-radius: 6px;
        }

        &:hover,
        &:focus {
          .ant-input-number-input {
            border-color: var(--ge-primary);
            box-shadow: 0 0 0 2px color-mix(in srgb, var(--ge-primary) 10%, transparent);
          }
        }
      }

      :deep(.ant-select) {
        .ant-select-selector {
          border-radius: 6px;
        }

        &:hover,
        &:focus {
          .ant-select-selector {
            border-color: var(--ge-primary);
            box-shadow: 0 0 0 2px color-mix(in srgb, var(--ge-primary) 10%, transparent);
          }
        }
      }

      :deep(.ant-input-textarea-show-count::after) {
        float: right;
        color: var(--ge-text-tertiary);
      }
    }
  }

  .crop-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 300px;
  }
}

@media (max-width: 576px) {
  .profile-info-page {
    .header-card {
      :deep(.ant-card-body) {
        padding: 20px;
      }
    }

    .info-edit {
      :deep(.ant-form-item-label) {
        label {
          font-size: 14px;
        }
      }
    }
  }
}

/* 教师端绿色渐变 */
:root[data-role='teacher'] .profile-info-page .header-card {
  background: linear-gradient(135deg, #059669 0%, #34d399 100%);
}

/* 暗色模式 */
:root.dark .profile-info-page .header-card {
  background: linear-gradient(135deg, #0d429a 0%, #5598eb 100%);
}

:root[data-role='teacher'].dark .profile-info-page .header-card {
  background: linear-gradient(135deg, #047857 0%, #34c77e 100%);
}
</style>
