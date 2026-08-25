import { Link } from 'react-router-dom'
import { logEvent } from '../utils/logEvent'
import type { PostingSummary } from '../types/posting'

interface PostingCardProps {
  posting: PostingSummary
}

function formatDeadline(deadline: string | null) {
  if (!deadline) return '상시 모집'
  return new Intl.DateTimeFormat('ko-KR', {
    month: 'short',
    day: 'numeric',
  }).format(new Date(`${deadline}T00:00:00`))
}

export default function PostingCard({ posting }: PostingCardProps) {
  return (
    <Link
      className="posting-card"
      to={`/postings/${posting.id}`}
      onClick={() => void logEvent('posting_card_click', {}, { postingId: posting.id })}
    >
      <div className="card-topline">
        <span className="company-name">{posting.company || '기업 미상'}</span>
        {posting.has_cover_letter && <span className="status-badge">자소서</span>}
      </div>
      <h2>{posting.title || '제목 없는 공고'}</h2>
      <p className="card-job">{posting.job_type || '직무 미기재'}</p>
      <div className="card-meta">
        <span>{posting.industry || '산업 미기재'}</span>
        <span className="deadline">마감 {formatDeadline(posting.deadline)}</span>
      </div>
      <span className="card-arrow" aria-hidden="true">↗</span>
    </Link>
  )
}