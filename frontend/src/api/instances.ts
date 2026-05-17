import { apiFetch, getApiBaseUrl } from './client'
import type { Instance, InstanceMetadata } from './types'

export function getInstance(id: number): Promise<Instance> {
  return apiFetch<Instance>(`/instances/${id}`)
}

export function getInstanceMetadata(id: number): Promise<InstanceMetadata> {
  return apiFetch<InstanceMetadata>(`/instances/${id}/metadata`)
}

// URL builder for Cornerstone's wadouri: scheme; not a fetch.
export function getInstanceFileUrl(id: number): string {
  return `${getApiBaseUrl()}/instances/${id}/file`
}
