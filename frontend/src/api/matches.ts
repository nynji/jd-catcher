import type { MatchAnalysis } from '../types/analysis'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const ANALYZE_TIMEOUT_MS = 60_000

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : null
    throw new Error(detail ?? `API 요청에 실패했습니다. (${response.status})`)
  }
  return response.json() as Promise<T>
}

export async function analyzeMatch(
  resumeId: number,
  roleId: number,
  force = false,
): Promise<MatchAnalysis> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), ANALYZE_TIMEOUT_MS)
  try {
    const response = await fetch(`${API_BASE_URL}/matches/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resume_id: resumeId, role_id: roleId, force }),
      signal: controller.signal,
    })
    return await readJson<MatchAnalysis>(response)
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('분석 응답 시간이 너무 오래 걸립니다. 잠시 후 다시 시도해주세요.')
    }
    throw error
  } finally {
    clearTimeout(timeout)
  }
}
