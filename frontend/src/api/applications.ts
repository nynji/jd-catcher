import type { ExplainResult } from '../types/matching'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export async function explainApplication(applicationId: number): Promise<ExplainResult> {
  const response = await fetch(`${API_BASE_URL}/applications/${applicationId}/explain`)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : null
    throw new Error(detail ?? `API 요청에 실패했습니다. (${response.status})`)
  }
  return response.json() as Promise<ExplainResult>
}
