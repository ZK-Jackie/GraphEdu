/**
 * 文件上传相关类型定义
 * 对应后端：graphedu/common/models/dto/upload.py 和 vo/upload.py
 */

// ============================================================================
// 请求 DTO 类型
// ============================================================================

/**
 * 上传文件参数
 */
export interface UploadFileDTO {
  /** 文件分类: 1-头像 2-课程封面 3-书籍封面 4-书籍文件 5-笔记附件 6-作业 7-课件 */
  fileCategory: number
  /** 访问级别: 0-私有 1-登录用户 2-公开 */
  accessLevel: string
  /** 是否允许下载: 0-否 1-是 */
  downloadFlag: string
  /** 备注信息 */
  remark?: string
}

// ============================================================================
// 响应 VO 类型
// ============================================================================

/**
 * 文件信息
 */
export interface FileInfoVO {
  /** 文件ID */
  fileId: number
  /** 文件原名称 */
  fileName: string
  /** 存储路径/URL/oss对象名 */
  filePath: string
  /** 文件大小（字节） */
  fileSize: number
  /** 文件类型（MIME类型） */
  fileType: string
  /** 文件分类: 1-头像 2-课程封面 3-书籍封面 4-书籍文件 5-笔记附件 6-作业 7-课件 */
  fileCategory: number
  /** 存储类型: 1-OSS 2-本地存储 */
  storageType: number
  /** 访问级别: 0-私有 1-登录用户 2-公开 */
  accessLevel: string
  /** 是否允许下载: 0-否 1-是 */
  downloadFlag: string
  /** 下载次数 */
  downloadCount: number
  /** 查看次数 */
  viewCount: number
  /** 被引用次数 */
  refCount: number
  /** 审核状态，对照 sys_upload_audit_status */
  auditStatus: '0' | '1' | '2' | '3'
  /** 审核者ID（如果有） */
  auditorId?: number
  /** 审核时间（ISO格式，如果有） */
  auditTime?: string
  /** 审核备注（如果有） */
  auditRemark?: string
  /** 上传文件状态，对照 sys_data_status（0正常 1停用 2已删除） */
  status: string
  /** 上传者IP地址 */
  createIp: string
  /** 上传用户ID */
  createBy: number
  /** 上传时间（ISO格式） */
  createTime: string
  /** 最后更新用户ID */
  updateBy?: number
  /** 最后更新时间（ISO格式） */
  updateTime?: string
  /** 备注信息 */
  remark?: string
}

/**
 * 文件下载信息
 */
export interface FileDownloadVO {
  /** 文件下载URL */
  fileUrl: string
  /** 文件下载直链URL */
  downloadUrl?: string
  /** 缩略图URL（如果为图片且有） */
  thumbnailUrl?: string
  /** 文件名称 */
  fileName: string
  /** 文件类型（MIME类型） */
  fileType: string
  /** 文件大小（字节） */
  fileSize: number
}
