const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export class ApiError extends Error {
  readonly status: number
  readonly body?: unknown

  constructor(status: number, message: string, body?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

interface ErrorBody {
  error?: string
  detail?: string
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, options)

  if (!response.ok) {
    let body: ErrorBody | undefined
    try {
      body = (await response.json()) as ErrorBody
    } catch {
      // body may not be JSON (e.g. empty 500); fall through to statusText
    }
    throw new ApiError(response.status, body?.error || body?.detail || response.statusText, body)
  }

  return response.json() as Promise<T>
}

export function getApiBaseUrl(): string {
  return API_BASE
}
