import { message, notification, Modal } from 'ant-design-vue'
import type { MessageArgsProps, ModalFuncProps } from 'ant-design-vue'
import type { NotificationArgsProps } from 'ant-design-vue/es/notification'

type Theme = 'info' | 'success' | 'warning' | 'error'

/**
 * 系统消息提示工具
 * @example
 * SystemMessage({ theme: 'info', content: '操作成功' })
 * SystemMessage({ theme: 'success', content: '保存成功', duration: 5000 })
 * SystemMessage({ theme: 'error', content: '操作失败', duration: 0 })
 */
export const SystemMessage = ({
  theme,
  content,
  options,
}: {
  theme: Theme
  content: string
  options?: Partial<MessageArgsProps>
}): void => {
  const defaultOptions: Partial<MessageArgsProps> = {
    duration: 3,
  }
  const mergedOptions = { ...defaultOptions, ...options }
  message[theme]({ content, ...mergedOptions })
}

/**
 * 系统通知工具
 * @example
 * SystemNotification({ theme: 'info', title: '通知标题', content: '详细内容' })
 * SystemNotification({ theme: 'success', title: '导出成功', content: '数据已生成', placement: 'topLeft' })
 * SystemNotification({ theme: 'error' })  // 使用默认标题
 */
export const SystemNotification = ({
  theme,
  title,
  content,
  options,
}: {
  theme: Theme
  title?: string
  content?: string
  options?: Partial<NotificationArgsProps>
}): void => {
  // 根据消息类型设置默认标题
  const defaultTitles: Record<Theme, string> = {
    info: '信息',
    success: '成功',
    warning: '警告',
    error: '错误',
  }

  notification[theme]({
    message: title || defaultTitles[theme],
    description: content || '',
    ...options,
  })
}

/**
 * 系统对话框工具（Callback-Promise 风格，例如 Ant Design）
 * 支持在 onOk 中返回 Promise 来处理异步操作（会显示 loading 状态）
 * @example
 * // 同步操作
 * SystemDialog({
 *   theme: 'warning',
 *   title: '警告',
 *   content: '此操作不可逆',
 *   confirmBtn: '继续',
 *   cancelBtn: '取消',
 *   onOk: () => console.log('确认'),
 *   onCancel: () => console.log('取消')
 * })
 *
 * // 异步操作（自动显示 loading）
 * SystemDialog({
 *   theme: 'info',
 *   title: '提示',
 *   content: '确定要删除吗？',
 *   confirmBtn: '确定',
 *   onOk: () => {
 *     return new Promise((resolve, reject) => {
 *       // 执行异步操作
 *       setTimeout(() => resolve(), 1000)
 *     })
 *   }
 * })
 */
export const SystemDialog = ({
  theme,
  title,
  content,
  confirmBtn,
  cancelBtn,
  onOk,
  onCancel,
  ...options
}: {
  theme: Theme
  title: string
  content: string
  confirmBtn: string
  cancelBtn?: string
  onOk?: () => void | Promise<void>
  onCancel?: () => void
} & Partial<ModalFuncProps>): ReturnType<typeof Modal.confirm> => {
  const modalMethod = theme === 'info' || theme === 'success' ? Modal[theme] : Modal.confirm

  return modalMethod({
    title,
    content,
    okText: confirmBtn,
    cancelText: cancelBtn,
    type: theme,
    onOk,
    onCancel,
    ...options,
  })
}

/**
 * 系统确认对话框（Promise 风格，例如 Element Plus）
 * @example
 * SystemConfirm({ theme: 'warning', title: '确认删除', content: '此操作不可逆', confirmBtn: '确定' })
 *   .then(() => {
 *     // 用户点击确定
 *     console.log('执行删除')
 *   })
 *   .catch(() => {
 *     // 用户点击取消或关闭
 *     console.log('取消操作')
 *   })
 */
export const SystemConfirm = ({
  theme,
  title,
  content,
  confirmBtn,
  cancelBtn,
  ...options
}: {
  theme: Theme
  title: string
  content: string
  confirmBtn: string
  cancelBtn?: string
} & Partial<ModalFuncProps>): Promise<void> => {
  return new Promise((resolve, reject) => {
    const modalMethod = theme === 'info' || theme === 'success' ? Modal[theme] : Modal.confirm

    modalMethod({
      title,
      content,
      okText: confirmBtn,
      cancelText: cancelBtn,
      type: theme,
      ...options,
      onOk: () => resolve(),
      onCancel: () => reject(),
    })
  })
}
