import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import PostingCard from '../components/PostingCard'
import { fetchPostings } from '../api/postings'
import type { PostingSort, PostingSummary } from '../types/posting'

function Spinner() {
  return <span className="spinner" aria-label="불러오는 중" />
}

export default function PostingListPage() {
  const [postings, setPostings] = useState<PostingSummary[]>([])
  const [sort, setSort] = useState<PostingSort>('collected_at')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    fetchPostings(1, 50, sort)
      .then((data) => {
        if (active) setPostings(data)
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : '공고를 불러오지 못했습니다.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [sort])

  return (
    <main className="page-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">JD CATCHER / OPEN ROLES</p>
          <h1>내 역량에 맞는<br /><em>기회를 고르세요.</em></h1>
          <p className="header-copy">직무명이 아닌, 공고 본문의 요구 역량을 기준으로 모은 인턴십입니다.</p>
        </div>
        <div className="header-side">
          <div className="header-stat"><strong>{loading ? '—' : postings.length}</strong><span>공고 수</span></div>
          <Link className="primary-button" to="/resume">이력서로 맞춤 공고 찾기 ↗</Link>
        </div>
      </header>

      <section className="toolbar" aria-label="공고 정렬">
        <span className="section-label">LATEST LISTINGS</span>
        <div className="sort-toggle">
          <button className={sort === 'collected_at' ? 'active' : ''} onClick={() => setSort('collected_at')}>수집순</button>
          <button className={sort === 'deadline' ? 'active' : ''} onClick={() => setSort('deadline')}>마감순</button>
        </div>
      </section>

      {loading && <div className="state-panel"><Spinner /><span>공고를 불러오는 중입니다</span></div>}
      {error && <div className="state-panel error-panel"><strong>연결할 수 없습니다.</strong><span>{error}</span></div>}
      {!loading && !error && postings.length === 0 && <div className="state-panel"><span>아직 수집된 공고가 없습니다.</span></div>}
      {!loading && !error && postings.length > 0 && (
        <section className="posting-grid" aria-label="공고 목록">
          {postings.map((posting) => <PostingCard key={posting.id} posting={posting} />)}
        </section>
      )}
    </main>
  )
}
