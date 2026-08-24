import type { PostingDetail, PostingSort, PostingSummary } from '../types/posting'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`)
  if (!response.ok) {
    throw new Error(`API 요청에 실패했습니다. (${response.status})`)
  }
  return response.json() as Promise<T>
}

export function fetchPostings(
  page = 1,
  size = 20,
  orderBy: PostingSort = 'collected_at',
): Promise<PostingSummary[]> {
  const params = new URLSearchParams({
    page: String(page),
    size: String(size),
    order_by: orderBy,
  })
  return request<PostingSummary[]>(`/postings?${params.toString()}`)
}

export function fetchPosting(postingId: number): Promise<PostingDetail> {
  return request<PostingDetail>(`/postings/${postingId}`)
}