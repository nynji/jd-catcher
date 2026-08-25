import { useEffect, useState } from 'react'
import type { CSSProperties } from 'react'
import { Link, useParams } from 'react-router-dom'
import { analyzeMatch } from '../api/matches'
import { fetchStoredMatches } from '../api/resumes'
import { logEvent } from '../utils/logEvent'
import { isCurrentResume } from '../utils/resumeSession'
import type { MatchAnalysis } from '../types/analysis'
import type { MatchResult } from '../types/matching'

type Status = 'loading' | 'done' | 'error'

function Spinner() {
  return <span className="spinner" aria-label="분석 중" />
}

function scoreTier(score: number) {
  if (score >= 70) return 'high'
  if (score >= 40) return 'mid'
  return 'low'
}

const STRENGTH_LABEL: Record<string, string> = { high: '높음', medium: '보통', low: '낮음' }

export default function MatchAnalysisPage() {
  const { resumeId, roleId } = useParams()
  const [posting, setPosting] = useState<MatchResult | null>(null)
  const [analysis, setAnalysis] = useState<MatchAnalysis | null>(null)
  const [status, setStatus] = useState<Status>('loading')
  const [error, setError] = useState<string | null>(null)
  const [retrying, setRetrying] = useState(false)

  useEffect(() => {
    if (!resumeId || !roleId) return
    if (!isCurrentResume(Number(resumeId))) {
      setError('이 세션에 등록된 이력서가 아닙니다. 이력서를 다시 등록해주세요.')
      setStatus('error')
      return
    }
    let active = true
    setStatus('loading')
    setError(null)
    Promise.all([fetchStoredMatches(Number(resumeId)), analyzeMatch(Number(resumeId), Number(roleId))])
      .then(([matches, analysisResult]) => {
        if (!active) return
        setPosting(matches.find((match) => match.role_id === Number(roleId)) ?? null)
        setAnalysis(analysisResult)
        setStatus('done')
        logEvent('match_analysis_view', {
          role_id: Number(roleId),
          ai_match_score: analysisResult.ai_match_score,
        })
      })
      .catch((reason: unknown) => {
        if (!active) return
        setError(reason instanceof Error ? reason.message : '분석 결과를 불러오지 못했습니다.')
        setStatus('error')
      })
    return () => {
      active = false
    }
  }, [resumeId, roleId])

  async function handleRetry() {
    if (!resumeId || !roleId) return
    setRetrying(true)
    setStatus('loading')
    setError(null)
    try {
      const result = await analyzeMatch(Number(resumeId), Number(roleId), true)
      setAnalysis(result)
      setStatus('done')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '분석에 실패했습니다.')
      setStatus('error')
    } finally {
      setRetrying(false)
    }
  }

  if (status === 'loading') {
    return (
      <main className="page-shell">
        <div className="state-panel full-page"><Spinner /><span>AI가 공고를 분석하고 있습니다...</span></div>
      </main>
    )
  }

  const isSessionMismatch = Boolean(resumeId) && !isCurrentResume(Number(resumeId))

  if (status === 'error' || !analysis) {
    return (
      <main className="page-shell">
        <div className="state-panel full-page error-panel">
          <strong>분석할 수 없습니다.</strong>
          <span>{error}</span>
          {isSessionMismatch ? (
            <Link to="/resume">이력서 등록하러 가기</Link>
          ) : (
            <button className="secondary-button" disabled={retrying} onClick={() => void handleRetry()}>
              {retrying ? '재시도 중...' : '다시 시도'}
            </button>
          )}
        </div>
      </main>
    )
  }

  const score = analysis.ai_match_score ?? 0
  const tier = scoreTier(score)

  return (
    <main className="analysis-shell">
      <Link className="back-link" to={resumeId ? `/match/${resumeId}` : '/resume'}>← 매칭 목록</Link>

      <section className="analysis-hero">
        <div>
          <p className="eyebrow">{posting?.company || '기업 미상'}</p>
          <h1>{posting?.title || '제목 없는 공고'}</h1>
          <p className="header-copy">{(posting?.role_name ?? '').split('\n')[0] || '직무 미기재'}</p>
          {analysis.score_reason && <p className="hero-summary">{analysis.score_reason}</p>}
        </div>
        <div className={`score-gauge tier-${tier}`} style={{ '--pct': score } as CSSProperties}>
          <div className="score-gauge-inner">
            <strong>{score}</strong>
            <span>%</span>
          </div>
        </div>
      </section>

      <div className="analysis-top-row">
        {analysis.summary && (
          <section>
            <p className="point-section-title">종합 평가</p>
            <p className="summary-text">{analysis.summary}</p>
          </section>
        )}

        {analysis.recommended_emphasis.length > 0 && (
          <section>
            <p className="point-section-title">강조 포인트</p>
            <ul className="emphasis-list">
              {analysis.recommended_emphasis.map((item, index) => <li key={index}>{item}</li>)}
            </ul>
          </section>
        )}
      </div>

      <div className="analysis-board">
        {analysis.matched_points.length > 0 && (
          <section>
            <p className="point-section-title">매칭 포인트</p>
            <div className="point-list">
              {analysis.matched_points.map((point, index) => (
                <div className="point-card point-matched" key={index}>
                  <div className="point-row">
                    <span className="point-label">내 역량</span>
                    <span className={`strength-badge strength-${point.strength}`}>
                      강도: {STRENGTH_LABEL[point.strength] ?? point.strength}
                    </span>
                  </div>
                  <p className="point-main">{point.applicant_capability}</p>
                  <div className="point-arrow">↓ 매칭</div>
                  <span className="point-label">공고 요구사항</span>
                  <p className="point-main">{point.jd_requirement}</p>
                  <p className="point-explanation">{point.explanation}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {analysis.gap_points.length > 0 && (
          <section>
            <p className="point-section-title">부족한 부분</p>
            <div className="point-list">
              {analysis.gap_points.map((point, index) => (
                <div className="point-card point-gap" key={index}>
                  <span className="point-label">요구사항</span>
                  <p className="point-main">{point.jd_requirement}</p>
                  <span className="point-label">현재 수준</span>
                  <p className="point-main muted">{point.current_state}</p>
                  <p className="point-explanation">{point.suggestion}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        <div className="analysis-actions">
          <button className="secondary-button" type="button" disabled title="준비 중인 기능입니다">
            자소서 초안 생성
          </button>
          {posting?.apply_url && (
            <a className="primary-button" href={posting.apply_url} target="_blank" rel="noreferrer">
              홈페이지 지원 ↗
            </a>
          )}
        </div>
      </div>
    </main>
  )
}
