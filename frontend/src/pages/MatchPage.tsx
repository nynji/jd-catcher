import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { fetchStoredMatches } from '../api/resumes'
import { explainApplication } from '../api/applications'
import { analyzeMatch } from '../api/matches'
import type { MatchResult } from '../types/matching'

function Spinner() {
  return <span className="spinner" aria-label="불러오는 중" />
}

function formatDeadline(deadline: string | null) {
  if (!deadline) return '상시 모집'
  return new Intl.DateTimeFormat('ko-KR', { month: 'short', day: 'numeric' }).format(
    new Date(`${deadline}T00:00:00`),
  )
}

function scoreTier(score: number) {
  if (score >= 70) return 'high'
  if (score >= 40) return 'mid'
  return 'low'
}

interface ExplainModalState {
  applicationId: number
  loading: boolean
  text: string | null
  error: string | null
}

export default function MatchPage() {
  const { resumeId } = useParams()
  const navigate = useNavigate()
  const [matches, setMatches] = useState<MatchResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [modal, setModal] = useState<ExplainModalState | null>(null)
  const [analyzingRoleId, setAnalyzingRoleId] = useState<number | null>(null)
  const [analyzeError, setAnalyzeError] = useState<string | null>(null)

  useEffect(() => {
    if (!resumeId) return
    setLoading(true)
    setError(null)
    fetchStoredMatches(Number(resumeId))
      .then(setMatches)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : '매칭 결과를 불러오지 못했습니다.'))
      .finally(() => setLoading(false))
  }, [resumeId])

  async function handleAnalyze(roleId: number) {
    if (!resumeId) return
    setAnalyzingRoleId(roleId)
    setAnalyzeError(null)
    try {
      await analyzeMatch(Number(resumeId), roleId)
      navigate(`/analysis/${resumeId}/${roleId}`)
    } catch (reason) {
      setAnalyzeError(reason instanceof Error ? reason.message : '분석에 실패했습니다.')
      setAnalyzingRoleId(null)
    }
  }

  async function handleExplain(applicationId: number) {
    setModal({ applicationId, loading: true, text: null, error: null })
    try {
      const result = await explainApplication(applicationId)
      setModal({ applicationId, loading: false, text: result.explanation, error: null })
    } catch (reason) {
      setModal({
        applicationId,
        loading: false,
        text: null,
        error: reason instanceof Error ? reason.message : '매칭 이유를 불러오지 못했습니다.',
      })
    }
  }

  return (
    <main className="page-shell">
      <Link className="back-link" to="/resume">← 이력서</Link>
      <header className="page-header">
        <div>
          <p className="eyebrow">MATCH RESULTS</p>
          <h1>내 역량에 맞는<br /><em>공고를 확인하세요.</em></h1>
          <p className="header-copy">역량 일치율이 높은 순으로 정렬했습니다.</p>
        </div>
        <div className="header-side">
          <div className="header-stat"><strong>{loading ? '—' : matches.length}</strong><span>매칭된 직무</span></div>
        </div>
      </header>

      {loading && <div className="state-panel"><Spinner /><span>매칭 결과를 불러오는 중입니다</span></div>}
      {error && <div className="state-panel error-panel"><strong>불러올 수 없습니다.</strong><span>{error}</span></div>}
      {analyzeError && (
        <div className="state-panel error-panel">
          <strong>상세 분석에 실패했습니다.</strong>
          <span>{analyzeError}</span>
        </div>
      )}
      {!loading && !error && matches.length === 0 && (
        <div className="state-panel"><span>매칭된 공고가 없습니다. 공고에 등록된 요구 역량이 아직 부족할 수 있습니다.</span></div>
      )}
      {!loading && !error && matches.length > 0 && (
        <section className="posting-grid" aria-label="매칭 결과">
          {matches.map((match) => (
            <Link className="posting-card" key={match.role_id} to={`/postings/${match.posting_id}`}>
              <div className="card-topline">
                <span className="company-name">{match.company || '기업 미상'}</span>
                <span className={`match-badge tier-${scoreTier(match.match_score)}`}>{match.match_score}%</span>
              </div>
              <h2>{match.title || '제목 없는 공고'}</h2>
              <p className="card-job">{(match.role_name ?? '').split('\n')[0] || '직무 미기재'}</p>
              <div className="card-meta">
                <span className="deadline">마감 {formatDeadline(match.deadline)}</span>
              </div>
              <div className="match-card-actions">
                {match.application_id != null && (
                  <button
                    type="button"
                    className="explain-button"
                    onClick={(event) => {
                      event.preventDefault()
                      event.stopPropagation()
                      void handleExplain(match.application_id as number)
                    }}
                  >
                    매칭 이유 보기
                  </button>
                )}
                <button
                  type="button"
                  className="explain-button"
                  disabled={analyzingRoleId === match.role_id}
                  onClick={(event) => {
                    event.preventDefault()
                    event.stopPropagation()
                    void handleAnalyze(match.role_id)
                  }}
                >
                  {analyzingRoleId === match.role_id ? (
                    <><Spinner /> 분석 중...</>
                  ) : (
                    '상세 분석 보기'
                  )}
                </button>
              </div>
            </Link>
          ))}
        </section>
      )}

      {modal && (
        <div className="modal-backdrop" onClick={() => setModal(null)}>
          <div className="modal-panel" onClick={(event) => event.stopPropagation()}>
            <button className="modal-close" aria-label="닫기" onClick={() => setModal(null)}>×</button>
            <h3>매칭 이유</h3>
            {modal.loading && <div className="state-panel"><Spinner /><span>생성 중입니다...</span></div>}
            {modal.error && <p className="muted">{modal.error}</p>}
            {modal.text && <p className="modal-text">{modal.text}</p>}
          </div>
        </div>
      )}
    </main>
  )
}
