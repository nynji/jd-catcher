import { useEffect } from 'react'
import { startEngagementTracking } from '../utils/engagement'
import type { EventIds } from '../utils/logEvent'
import { logEvent } from '../utils/logEvent'

/**
 * 페이지 진입 시 조회(view) 이벤트를 1회 기록하고, 그 이벤트 행에 대한 체류/스크롤
 * 측정을 시작한다. 라우트 전환(언마운트) 시 측정을 종료하고 결과를 전송한다.
 */
export function usePageView(name: string, properties?: Record<string, unknown>, ids?: EventIds) {
  useEffect(() => {
    let cancelled = false
    let stop: (() => void) | undefined

    logEvent(name, properties, ids).then((eventId) => {
      if (cancelled || eventId == null) return
      stop = startEngagementTracking(eventId)
    })

    return () => {
      cancelled = true
      stop?.()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
}

/**
 * 조회 이벤트의 properties가 비동기로 로드되는 데이터에 의존해서(예: match_count)
 * usePageView처럼 마운트 시 바로 logEvent를 호출할 수 없는 페이지용.
 * 데이터가 준비된 시점에 직접 logEvent를 호출해 얻은 eventId를 넘기면 그때부터 추적을 시작한다.
 */
export function useEngagement(eventId: number | null) {
  useEffect(() => {
    if (eventId == null) return
    const stop = startEngagementTracking(eventId)
    return () => stop()
  }, [eventId])
}
