const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

/**
 * 페이지뷰 이벤트의 체류 시간 / 최대 스크롤 깊이를 측정해서, 그 이벤트 행에 나중에
 * 채워 넣는다(§5: 별도 이벤트가 아니라 UPDATE). SPA라 라우트 전환 시 pagehide/visibilitychange가
 * 안 일어날 수 있으므로, 컴포넌트 언마운트(stop 호출) 시점에도 fetch keepalive로 flush한다.
 * - 체류 시간: 탭이 백그라운드인 동안은 세지 않는다(visibilitychange로 일시정지/재개).
 * - 스크롤 깊이: 내려간 최댓값만 유지, 0~100 정수.
 */
export function startEngagementTracking(eventId: number): () => void {
  let activeStart: number | null = Date.now()
  let accumulatedMs = 0
  let maxScrollPct = 0
  let scrollScheduled = false
  let flushed = false

  function currentDurationMs(): number {
    const activeMs = activeStart != null ? Date.now() - activeStart : 0
    return accumulatedMs + activeMs
  }

  function measureScroll() {
    scrollScheduled = false
    const doc = document.documentElement
    const scrollable = doc.scrollHeight - window.innerHeight
    const pct = scrollable > 0 ? ((window.scrollY + window.innerHeight) / doc.scrollHeight) * 100 : 100
    maxScrollPct = Math.max(maxScrollPct, Math.min(100, Math.round(pct)))
  }

  function onScroll() {
    if (scrollScheduled) return
    scrollScheduled = true
    requestAnimationFrame(measureScroll)
  }

  function flush(final: boolean) {
    if (final && flushed) return
    if (final) flushed = true

    const payload = JSON.stringify({
      duration_ms: currentDurationMs(),
      max_scroll_depth_pct: maxScrollPct,
    })
    const url = `${API_BASE_URL}/events/${eventId}/engagement`

    if (final && navigator.sendBeacon) {
      navigator.sendBeacon(url, new Blob([payload], { type: 'application/json' }))
      return
    }
    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: payload,
      keepalive: true,
    }).catch(() => undefined)
  }

  function onVisibilityChange() {
    if (document.visibilityState === 'hidden') {
      if (activeStart != null) {
        accumulatedMs += Date.now() - activeStart
        activeStart = null
      }
      flush(false)
    } else {
      activeStart = Date.now()
    }
  }

  function onPageHide() {
    flush(true)
  }

  window.addEventListener('scroll', onScroll, { passive: true })
  document.addEventListener('visibilitychange', onVisibilityChange)
  window.addEventListener('pagehide', onPageHide)
  measureScroll()

  return function stop() {
    window.removeEventListener('scroll', onScroll)
    document.removeEventListener('visibilitychange', onVisibilityChange)
    window.removeEventListener('pagehide', onPageHide)
    flush(true)
  }
}
