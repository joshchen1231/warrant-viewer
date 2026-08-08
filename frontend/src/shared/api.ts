import type { DataStatus, RealtimeResponse, UnderlyingResult, WarrantListResponse } from './types'

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const body = await res.json()
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

export async function searchUnderlying(q: string): Promise<UnderlyingResult[]> {
  const body = await getJson<{ results: UnderlyingResult[] }>(
    `/api/underlying/search?q=${encodeURIComponent(q)}`,
  )
  return body.results
}

export async function listWarrants(params: URLSearchParams): Promise<WarrantListResponse> {
  return getJson(`/api/warrants?${params.toString()}`)
}

export async function realtimeQuotes(codes: string[]): Promise<RealtimeResponse> {
  return getJson(`/api/realtime?codes=${encodeURIComponent(codes.join(','))}`)
}

export async function dataStatus(): Promise<DataStatus> {
  return getJson('/api/data/status')
}
