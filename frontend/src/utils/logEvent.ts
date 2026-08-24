/** 분석용 이벤트 로깅. 현재는 콘솔에만 기록한다(별도 분석 인프라 연결 전). */
export function logEvent(name: string, properties?: Record<string, unknown>) {
  // eslint-disable-next-line no-console
  console.info(`[event] ${name}`, properties ?? {})
}
