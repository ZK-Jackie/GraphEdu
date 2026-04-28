import useFunctionStore from '@/stores/modules/function'
import useUserStore from '@/stores/modules/user'
import type { Directive, DirectiveBinding } from 'vue'

/**
 * v-permit 自定义指令
 *
 * 根据权限标识控制元素的显示/隐藏。
 * 无权限时元素会从 DOM 中移除（非隐藏）。
 *
 * 检查逻辑：
 * 1. 超级管理员（permissions 含 "*:*:*"）直接放行
 * 2. 在菜单树（DIR/MENU）中查找 functionKey
 * 3. 在用户权限列表（含 BUTTON/INTERFACE）中查找 functionKey
 *
 * @example
 * <!-- 单个权限 -->
 * <button v-permit="'admin:education:chapter:add'">新增章节</button>
 *
 * <!-- 多个权限（任一满足即显示） -->
 * <button v-permit="['admin:education:chapter:edit', 'admin:education:chapter:delete']">操作</button>
 */
export const vPermit: Directive<HTMLElement, string | string[]> = {
  mounted(el: HTMLElement, binding: DirectiveBinding<string | string[]>) {
    const { value } = binding
    if (!value) return

    const functionStore = useFunctionStore()
    const userStore = useUserStore()
    const keys = Array.isArray(value) ? value : [value]

    // 超级管理员通配符
    const userPerms = userStore.permissions
    if (userPerms.includes('*:*:*')) return

    const hasAny = keys.some((key) => functionStore.hasPermission(key) || userPerms.includes(key))
    if (!hasAny) {
      el.parentNode?.removeChild(el)
    }
  },
}
