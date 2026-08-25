import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import PostingCard from '../components/PostingCard'
import { fetchPostingCount, fetchPostings } from '../api/postings'
import { usePageView } from '../hooks/usePageView'
import { logEvent } from '../utils/logEvent'
import type { PostingSort, PostingSummary } from '../types/posting'

const PAGE_SIZE = 50

function Spinner() {
  return <span className="spinner" aria-label="불러오는 중" />
}

function getPageNumbers(current: number, total: number): (number | 'ellipsis')[] {
  const window = 2
  const pages: (number | 'ellipsis')[] = []
  for (let p = 1; p <= total; p++) {
    if (p === 1 || p === total || (p >= current - window && p <= current + window)) {
      pages.push(p)
    } else if (pages[pages.length - 1] !== 'ellipsis') {
      pages.push('ellipsis')
    }
  }
  return pages
}

export default function PostingListPage() {
  const [postings, setPostings] = useState<PostingSummary[]>([])
  const [total, setTotal] = useState<number | null>(null)
  const [sort, setSort] = useState<PostingSort>('collected_at')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  usePageView('posting_list_view', { sort, page })

  useEffect(() => {
    fetchPostingCount()
      .then(setTotal)
      .catch(() => undefined)
  }, [])

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    fetchPostings(page, PAGE_SIZE, sort)
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
  }, [sort, page])

  function handleSortChange(nextSort: PostingSort) {
    setSort(nextSort)
    setPage(1)
    void logEvent('posting_sort_change', { sort: nextSort })
  }

  function handlePageChange(nextPage: number) {
    if (nextPage === page) return
    setPage(nextPage)
    window.scrollTo({ top: 0, behavior: 'smooth' })
    void logEvent('posting_page_change', { page: nextPage })
  }

  const totalPages = total != null ? Math.max(1, Math.ceil(total / PAGE_SIZE)) : null

  return (
    <main className="page-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">JD CATCHER / OPEN ROLES</p>
          <h1>수집된 채용공고를<br /><em>모두 확인하세요.</em></h1>
          <p className="header-copy">공고 원문 그대로, 필터링 없이 모은 목록입니다. 이력서를 올리면 내 역량에 맞는 공고만 따로 확인할 수 있어요.</p>
        </div>
        <div className="header-side">
          <div className="header-stat"><strong>{total ?? '—'}</strong><span>공고 수</span></div>
          <Link className="primary-button" to="/resume">이력서로 맞춤 공고 찾기 ↗</Link>
        </div>
      </header>

      <section className="toolbar" aria-label="공고 정렬">
        <span className="section-label">LATEST LISTINGS</span>
        <div className="sort-toggle">
          <button className={sort === 'collected_at' ? 'active' : ''} onClick={() => handleSortChange('collected_at')}>수집순</button>
          <button className={sort === 'deadline' ? 'active' : ''} onClick={() => handleSortChange('deadline')}>마감순</button>
        </div>
      </section>

      {loading && <div className="state-panel"><Spinner /><span>공고를 불러오는 중입니다</span></div>}
      {error && <div className="state-panel error-panel"><strong>연결할 수 없습니다.</strong><span>{error}</span></div>}
      {!loading && !error && postings.length === 0 && <div className="state-panel"><span>아직 수집된 공고가 없습니다.</span></div>}
      {!loading && !error && postings.length > 0 && (
        <>
          <section className="posting-grid" aria-label="공고 목록">
            {postings.map((posting) => <PostingCard key={posting.id} posting={posting} />)}
          </section>
          {totalPages != null && totalPages > 1 && (
            <nav className="pagination" aria-label="페이지 네비게이션">
              <button
                className="page-nav"
                disabled={page === 1}
                onClick={() => handlePageChange(page - 1)}
                aria-label="이전 페이지"
              >
                ‹
              </button>
              {getPageNumbers(page, totalPages).map((entry, index) =>
                entry === 'ellipsis' ? (
                  <span className="page-ellipsis" key={`ellipsis-${index}`}>…</span>
                ) : (
                  <button
                    key={entry}
                    className={`page-number${entry === page ? ' active' : ''}`}
                    onClick={() => handlePageChange(entry)}
                    aria-current={entry === page ? 'page' : undefined}
                  >
                    {entry}
                  </button>
                ),
              )}
              <button
                className="page-nav"
                disabled={page === totalPages}
                onClick={() => handlePageChange(page + 1)}
                aria-label="다음 페이지"
              >
                ›
              </button>
            </nav>
          )}
        </>
      )}
    </main>
  )
}
