import { apiFetch } from './client'
import type { Series, Study } from './types'

interface ListStudiesResponse {
  studies: Study[]
}

interface ListSeriesResponse {
  series: Series[]
}

export async function listStudies(): Promise<Study[]> {
  const response = await apiFetch<ListStudiesResponse>('/studies')
  return response.studies
}

export async function listSeriesForStudy(studyId: number): Promise<Series[]> {
  const response = await apiFetch<ListSeriesResponse>(`/studies/${studyId}/series`)
  return response.series
}
