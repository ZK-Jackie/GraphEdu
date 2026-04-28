import defAva from '@/assets/avatar/default-0.png'
import type {
  UserLoginByUsernameDTO,
  UserLoginByPhoneDTO,
  UserLoginByStudentNoDTO,
  UserLoginByTeacherNoDTO,
} from '@/types/api/system/user.ts'
import { getInfo, login, loginByPhone, loginByStudentNo, loginByTeacherNo, logout } from '@/api/system/auth'
import { getToken, removeToken, setToken } from '@/utils/token.ts'
import { isEmpty, isHttp } from '@/utils/string.ts'
import { resetDynamicRoutesState } from '@/router/guard'
import useFunctionStore from './function'
import type { StudentDetailVO } from '@/types/api/education/student.ts'
import type { TeacherDetailVO } from '@/types/api/education/teacher.ts'

interface UserState {
  token?: string
  userId: string
  userName: string
  avatar: string
  roles: string[]
  permissions: string[]
  /** 学生信息 */
  studentInfo?: StudentDetailVO
  /** 教师信息 */
  teacherInfo?: TeacherDetailVO
  /** 当前激活的角色视角 */
  activeRole: 'student' | 'teacher' | 'admin' | null
}

const useUserStore = defineStore('user', {
  state: (): UserState => ({
    token: getToken(),
    userId: '',
    userName: '',
    avatar: '',
    roles: [],
    permissions: [],
    studentInfo: undefined,
    teacherInfo: undefined,
    activeRole: null,
  }),
  getters: {
    /**
     * 检查用户是否已登录
     */
    isLoggedIn(): boolean {
      return !!this.token
    },
    /**
     * 检查是否为学生
     */
    isStudent(): boolean {
      return !!this.studentInfo
    },
    /**
     * 检查是否为教师
     */
    isTeacher(): boolean {
      return !!this.teacherInfo
    },
    /**
     * 是否拥有多个角色（同时是学生和教师）
     */
    hasMultipleRoles(): boolean {
      return !!this.studentInfo && !!this.teacherInfo
    },
    /**
     * 检查是否为管理员（通过 ROLE_ADMIN 角色）
     */
    isAdmin(): boolean {
      return (this as any).hasRole('ROLE_ADMIN')
    },
    /**
     * 获取用户可用的角色列表
     */
    availableRoles(): Array<{ key: 'student' | 'teacher' | 'admin'; label: string }> {
      const roles: Array<{ key: 'student' | 'teacher' | 'admin'; label: string }> = []
      if (this.studentInfo) roles.push({ key: 'student', label: '学生' })
      if (this.teacherInfo) roles.push({ key: 'teacher', label: '教师' })
      if (this.isAdmin && !this.isStudent && !this.isTeacher) {
        roles.push({ key: 'admin', label: '管理员' })
      }
      return roles
    },
    /**
     * 当前激活角色的标签
     */
    activeRoleLabel(): string {
      if (this.activeRole === 'student') return '学生'
      if (this.activeRole === 'teacher') return '教师'
      if (this.activeRole === 'admin') return '管理员'
      return ''
    },
  },
  actions: {
    /**
     * 用户登录
     * @param loginType 登录类型
     * @param userInfo 登录信息
     */
    async login(
      loginType: 'username' | 'phone' | 'studentId' | 'employeeId',
      userInfo: UserLoginByUsernameDTO | UserLoginByPhoneDTO | UserLoginByStudentNoDTO | UserLoginByTeacherNoDTO
    ): Promise<void> {
      try {
        let resp: { data: { accessToken: string } }

        switch (loginType) {
          case 'phone':
            resp = await loginByPhone(userInfo as UserLoginByPhoneDTO)
            break
          case 'studentId':
            resp = await loginByStudentNo(userInfo as UserLoginByStudentNoDTO)
            break
          case 'employeeId':
            resp = await loginByTeacherNo(userInfo as UserLoginByTeacherNoDTO)
            break
          default: {
            const { username, password, code, uuid } = userInfo as UserLoginByUsernameDTO
            resp = await login({ username: username.trim(), password, code, uuid })
            break
          }
        }

        setToken(resp.data.accessToken)
        this.token = resp.data.accessToken
      } catch (error) {
        console.error('[User Store] 登录失败:', error)
        throw error
      }
    },

    /**
     * 获取用户信息
     */
    async fetchUserInfo(): Promise<void> {
      try {
        const res = await getInfo()
        const { user, student, teacher } = res.data.detail

        let avatar = res.data.detail.avatarUrl ?? ''
        if (!isHttp(avatar)) {
          avatar = isEmpty(avatar) ? defAva : import.meta.env.VITE_API_BASE_URL + avatar
        }

        if (res.data.roleKeys && res.data.roleKeys.length > 0) {
          this.roles = res.data.roleKeys
          this.permissions = res.data.permissions
        } else {
          this.roles = ['ROLE_DEFAULT']
        }

        this.userId = String(user.userId)
        this.userName = user.userName
        this.avatar = avatar

        // 保存学生/教师信息
        this.studentInfo = student
        this.teacherInfo = teacher

        // 初始化默认角色：优先学生，默认首页为学生视角
        if (!this.activeRole) {
          if (this.studentInfo) {
            this.activeRole = 'student'
          } else if (this.teacherInfo) {
            this.activeRole = 'teacher'
          } else if (this.isAdmin) {
            this.activeRole = 'admin'
          }
        }

        console.log('[User Store] 用户信息加载成功:', this.userName)
      } catch (error) {
        console.error('[User Store] 获取用户信息失败:', error)
        throw error
      }
    },

    /**
     * 退出登录
     */
    async logout(): Promise<void> {
      try {
        await logout()
      } catch (error) {
        console.error('[User Store] 退出登录接口调用失败:', error)
      } finally {
        // 无论接口是否成功，都清除本地数据
        this.clearUserData()
      }
    },

    /**
     * 清除用户数据
     */
    clearUserData(): void {
      this.token = ''
      this.userId = ''
      this.userName = ''
      this.avatar = ''
      this.roles = []
      this.permissions = []
      this.studentInfo = undefined
      this.teacherInfo = undefined
      this.activeRole = null
      removeToken()

      // 清除菜单和动态路由
      const functionStore = useFunctionStore()
      functionStore.clearMenuData()

      // 重置路由守卫状态
      resetDynamicRoutesState()

      console.log('[User Store] 用户数据已清除')
    },

    /**
     * 检查是否有指定权限
     * @param permission 权限标识
     */
    hasPermission(permission: string): boolean {
      return this.permissions.includes(permission)
    },

    /**
     * 检查是否有指定角色
     * @param role 角色标识
     */
    hasRole(role: string): boolean {
      return this.roles.includes(role)
    },

    /**
     * 切换激活的角色视角
     * @param role 目标角色
     */
    setActiveRole(role: 'student' | 'teacher' | 'admin'): void {
      // 安全检查：只有拥有对应身份才能切换
      if (role === 'student' && !this.studentInfo) return
      if (role === 'teacher' && !this.teacherInfo) return
      if (role === 'admin' && !this.isAdmin) return
      this.activeRole = role
    },
  },
})

export default useUserStore
