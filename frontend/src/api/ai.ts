import { apiFetch } from './client'
import type { AIResultResponse, AISegmentResponse } from './types'

export function triggerSegmentation(instanceId: number): Promise<AISegmentResponse> {
  return apiFetch<AISegmentResponse>(`/ai/segment/${instanceId}`, { method: 'POST' })
}

// 一律帶 ?status=completed：只取最新一筆 completed，繞過「失敗重跑寫的 error
// 紀錄遮蔽好結果」（後端問題 B，2026-06-15 已修並提供此參數，見 HANDOFF §3.3）。
// 省略則回任意最新（向後相容），但前端撈結果 / 做 overlay 一律帶。
export function getResult(instanceId: number): Promise<AIResultResponse> {
  return apiFetch<AIResultResponse>(`/ai/result/${instanceId}?status=completed`)
}
