import { apiFetch } from './client'
import type { AIResultResponse, AISegmentResponse } from './types'

export function triggerSegmentation(instanceId: number): Promise<AISegmentResponse> {
  return apiFetch<AISegmentResponse>(`/ai/segment/${instanceId}`, { method: 'POST' })
}

export function getResult(instanceId: number): Promise<AIResultResponse> {
  return apiFetch<AIResultResponse>(`/ai/result/${instanceId}`)
}
