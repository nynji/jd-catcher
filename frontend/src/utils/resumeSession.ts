/**
 * 서버에 별도 로그인/세션이 없어서, "한 번 등록한 이력서는 이 브라우저 세션에서만
 * 계속 볼 수 있다"는 요구를 sessionStorage로 구현한다.
 * - sessionStorage는 탭/브라우저를 닫으면 사라지고, 다른 사람의 세션과 공유되지 않는다.
 * - 이 값과 일치하지 않는 resumeId로 접근하면 매칭/분석 페이지에서 막는다.
 */
const KEY = 'currentResumeId'

export function getCurrentResumeId(): number | null {
  const raw = sessionStorage.getItem(KEY)
  if (!raw) return null
  const id = Number(raw)
  return Number.isFinite(id) ? id : null
}

export function setCurrentResumeId(id: number) {
  sessionStorage.setItem(KEY, String(id))
}

export function isCurrentResume(id: number): boolean {
  return getCurrentResumeId() === id
}
