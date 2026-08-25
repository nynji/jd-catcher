import { getAnonymousId, getEventSessionId } from './eventSession'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface EventIds {
  postingId?: number
  roleId?: number
  resumeId?: number
}

/**
 * 분석용 이벤트 로깅. 실패해도 화면 동작에는 절대 영향을 주지 않는다(fire-and-forget).
 * 저장된 이벤트 행의 id를 반환한다 — 조회(view) 이벤트는 이 id로 나중에 체류/스크롤을 채운다.
 */
export async function logEvent(
  name: string,
  properties?: Record<string, unknown>,
  ids?: EventIds,
): Promise<number | null> {
  const body = JSON.stringify({
    event_name: name,
    anonymous_id: getAnonymousId(),
    session_id: getEventSessionId(),
    path: window.location.pathname,
    properties: properties ?? {},
    posting_id: ids?.postingId,
    role_id: ids?.roleId,
    resume_id: ids?.resumeId,
  })
  try {
    const response = await fetch(`${API_BASE_URL}/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
      keepalive: true,
    })
    if (!response.ok) return null
    const data = (await response.json()) as { id: number | null }
    return data.id ?? null
  } catch {
    return null
  }
}
