/**
 * 이벤트 로깅용 익명 식별자.
 * - anonymous_id: localStorage에 UUID 하나를 보관해 브라우저 재방문 간에도 유지되는 장기 식별자.
 * - session_id: resumeSession.ts와 동일하게 sessionStorage 기반(탭 닫으면 초기화).
 * 로그인이 없는 서비스라 "누가"를 특정하는 용도가 아니라, 같은 사람의 여정을 묶어보는 용도다.
 */
const ANONYMOUS_ID_KEY = 'anonymousId'
const SESSION_ID_KEY = 'eventSessionId'

function createId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export function getAnonymousId(): string {
  let id = localStorage.getItem(ANONYMOUS_ID_KEY)
  if (!id) {
    id = createId()
    localStorage.setItem(ANONYMOUS_ID_KEY, id)
  }
  return id
}

export function getEventSessionId(): string {
  let id = sessionStorage.getItem(SESSION_ID_KEY)
  if (!id) {
    id = createId()
    sessionStorage.setItem(SESSION_ID_KEY, id)
  }
  return id
}
