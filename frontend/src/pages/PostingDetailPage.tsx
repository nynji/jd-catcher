import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchPosting } from '../api/postings'
import type { PostingDetail } from '../types/posting'

function formatDate(value: string | null) {
  if (!value) return '상시 모집'
  return new Intl.DateTimeFormat('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' }).format(new Date(`${value}T00:00:00`))
}

function Spinner() {
  return <span className="spinner" aria-label="불러오는 중" />
}

function PostingImage({ src, alt }: { src: string; alt: string }) {
  const [failed, setFailed] = useState(false)
  if (failed) return <div className="raw-image-fallback">{alt}</div>
  return <img className="raw-image" src={src} alt={alt} loading="lazy" onError={() => setFailed(true)} />
}

export default function PostingDetailPage() {
  const { postingId } = useParams()
  const [posting, setPosting] = useState<PostingDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!postingId) return
    fetchPosting(Number(postingId))
      .then(setPosting)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : '상세 정보를 불러오지 못했습니다.'))
      .finally(() => setLoading(false))
  }, [postingId])

  if (loading) return <div className="state-panel full-page"><Spinner /><span>공고 상세를 불러오는 중입니다</span></div>
  if (error || !posting) return <div className="state-panel full-page error-panel"><strong>공고를 찾을 수 없습니다.</strong><span>{error}</span><Link to="/">목록으로 돌아가기</Link></div>

  return (
    <main className="detail-shell">
      <Link className="back-link" to="/">← 공고 목록</Link>
      <header className="detail-header">
        <p className="eyebrow">{posting.industry || 'OPEN POSITION'}</p>
        <p className="detail-company">{posting.company || '기업 미상'}</p>
        <h1>{posting.title || '제목 없는 공고'}</h1>
        <p className="detail-job">{posting.job_type || '직무 미기재'}</p>
        <div className="detail-actions">
          {posting.apply_url && <a className="primary-button" href={posting.apply_url} target="_blank" rel="noreferrer">홈페이지 지원 ↗</a>}
          <button className="secondary-button" onClick={() => undefined}>관심 공고 추가</button>
        </div>
      </header>

      <section className="facts-grid">
        <div><span>산업</span><strong>{posting.industry || '미기재'}</strong></div>
        <div><span>근무지역</span><strong>{posting.location || '미기재'}</strong></div>
        <div><span>지원 마감</span><strong>{formatDate(posting.deadline)}</strong></div>
      </section>

      <div className="detail-columns">
        <div className="detail-main">
          <section className="content-section">
            <div className="section-heading"><span className="section-number">01</span><h2>제출사항</h2></div>
            {posting.submission_requirements.length > 0 ? <div className="requirement-list">{posting.submission_requirements.map((item) => <div className="requirement-row" key={item.id}><span className="requirement-type">{item.type}</span><span>{item.detail || (item.is_required ? '필수 제출' : '선택 제출')}</span></div>)}</div> : <p className="muted">등록된 제출사항이 없습니다.</p>}
          </section>
          <section className="content-section">
            <div className="section-heading"><span className="section-number">02</span><h2>공고 원문</h2></div>
            {posting.raw_text || posting.image_urls.length > 0 ? (
              <div className="raw-content">
                {posting.raw_text && <pre className="raw-text-block">{posting.raw_text}</pre>}
                {posting.image_urls.length > 0 && (
                  <div className="raw-image-list">
                    {posting.image_urls.map((src, index) => (
                      <PostingImage key={src} src={src} alt={`공고 원문 이미지 ${index + 1}`} />
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <p className="muted">공고 원문을 불러올 수 없습니다.</p>
            )}
          </section>

          <hr className="section-divider" />

          <section className="content-section">
            <div className="section-heading"><span className="section-number">03</span><h2>자소서 문항</h2></div>
            {posting.cover_letter_questions.length > 0 ? <div className="question-list">{posting.cover_letter_questions.map((question) => <article className="question-item" key={question.id}><div className="question-meta"><span>{question.role_name || '공통 문항'}</span>{question.char_limit && <small>{question.char_limit.toLocaleString()}자</small>}</div><p>{question.question_text}</p></article>)}</div> : <p className="muted">등록된 자소서 문항이 없습니다.</p>}
          </section>
        </div>
        <aside className="source-panel"><span className="section-label">SOURCE</span><p>링커리어 원문에서 수집한 공고입니다.</p><a href={posting.linkareer_url} target="_blank" rel="noreferrer">원문 보기 ↗</a></aside>
      </div>
    </main>
  )
}