/**
 * Admin 仪表盘 API
 * 对应后端：graphedu/api/services/system/admin_dashboard.py
 */
import request from '@/utils/request'
import type { ResponseType } from '@/types/api/common.ts'
import type { AdminDashboardSummaryVO } from '@/types/api/system/adminDashboard.ts'

/**
 * 获取管理员仪表盘总览统计
 * GET /system/admin/dashboard/overview
 */
export function getAdminDashboardOverview(): Promise<ResponseType<AdminDashboardSummaryVO>> {
  return request({
    url: '/system/admin/dashboard/overview',
    method: 'get',
  })
}
