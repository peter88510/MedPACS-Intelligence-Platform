import { apiFetch } from './client'
import type { Instance } from './types'

interface ListInstancesResponse {
  instances: Instance[]
}

export async function listInstancesForSeries(seriesId: number): Promise<Instance[]> {
  const response = await apiFetch<ListInstancesResponse>(`/series/${seriesId}/instances`)
  return response.instances
}
