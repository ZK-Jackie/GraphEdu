/**
 * 文件上传相关 API
 * 对应后端：graphedu/api/services/system/upload.py
 */
import request from '@/utils/request'
import type { ResponseType } from '@/types/api/common.ts'
import type { FileInfoVO, FileDownloadVO, UploadFileDTO } from '@/types/api/system/upload.ts'

/**
 * 上传文件到OSS
 * POST /common/upload
 */
export function uploadFile(file: File, uploadInfo: UploadFileDTO): Promise<ResponseType<FileInfoVO>> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('file_category', String(uploadInfo.fileCategory))
  formData.append('access_level', uploadInfo.accessLevel)
  formData.append('download_flag', uploadInfo.downloadFlag)
  if (uploadInfo.remark) {
    formData.append('remark', uploadInfo.remark)
  }

  return request({
    url: '/common/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

/**
 * 从OSS下载文件
 * GET /common/download/{file_id}
 */
export function downloadFile(fileId: number): Promise<ResponseType<FileDownloadVO>> {
  return request({
    url: `/common/download/${fileId}`,
    method: 'get',
  })
}

/**
 * 获取文件信息
 * GET /common/fileInfo/{file_id}
 */
export function getFileInfo(fileId: number): Promise<ResponseType<FileInfoVO>> {
  return request({
    url: `/common/fileInfo/${fileId}`,
    method: 'get',
  })
}

/**
 * 上传用户头像（专用接口）
 * POST /common/avatar
 */
export function uploadAvatar(file: File): Promise<ResponseType<FileInfoVO>> {
  const formData = new FormData()
  formData.append('file', file)

  return request({
    url: '/common/avatar',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}
