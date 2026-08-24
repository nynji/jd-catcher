import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { fetchStoredMatches } from '../api/resumes'
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

export default function MatchPage() {
  const { resumeId } = useParams()
  const navigate = useNavigate()
  const [matches, setMatches] = useState<MatchResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
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

  // 백엔드가 이미 match_score 내림차순으로 반환하지만, 프론트에서도 동일 기준을 보장한다.
  const sortedMatches = [...matches].sort((a, b) => b.match_score - a.match_score)

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
          <div className="header-stat"><strong>{loading ? '—' : sortedMatches.length}</strong><span>매칭된 직무</span></div>
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
      {!loading && !error && sortedMatches.length === 0 && (
        <div className="state-panel"><span>매칭된 공고가 없습니다. 이력서를 업로드하고 매칭을 다시 시작해보세요.</span></div>
      )}
      {!loading && !error && sortedMatches.length > 0 && (
        <section className="posting-grid" aria-label="매칭 결과">
          {sortedMatches.map((match) => (
            <Link className="posting-card match-card" key={match.role_id} to={`/postings/${match.posting_id}`}>
              <div className="card-topline">
                <span className="company-name">{match.company || '기업 미상'}</span>
                <span className={`match-badge tier-${scoreTier(match.match_score)}`}>{match.match_score}%</span>
              </div>
              <h2>{match.title || '제목 없는 공고'}</h2>
              <p className="card-job">{(match.role_name ?? '').split('\n')[0] || '직무 미기재'}</p>
              {match.reason && <p className="match-reason">{match.reason}</p>}
              <div className="card-meta">
                <span className="deadline">마감 {formatDeadline(match.deadline)}</span>
              </div>
              <div className="match-card-actions">
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
    </main>
  )
}
