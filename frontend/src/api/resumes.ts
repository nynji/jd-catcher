import type { MemberSkill, ResumeSummary, ResumeUploadResult } from '../types/resume'
import type { MatchResult } from '../types/matching'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : null
    throw new Error(detail ?? `API 요청에 실패했습니다. (${response.status})`)
  }
  return response.json() as Promise<T>
}

export function uploadResume(files: File[], title: string): Promise<ResumeUploadResult> {
  const formData = new FormData()
  for (const file of files) formData.append('files', file)
  if (title) formData.append('title', title)
  return fetch(`${API_BASE_URL}/resumes`, { method: 'POST', body: formData }).then((response) =>
    readJson<ResumeUploadResult>(response),
  )
}

export function fetchResumes(): Promise<ResumeSummary[]> {
  return fetch(`${API_BASE_URL}/resumes`).then((response) => readJson<ResumeSummary[]>(response))
}

export function fetchResumeSkills(resumeId: number): Promise<MemberSkill[]> {
  return fetch(`${API_BASE_URL}/resumes/${resumeId}/skills`).then((response) =>
    readJson<MemberSkill[]>(response),
  )
}

export function startMatching(resumeId: number): Promise<MatchResult[]> {
  return fetch(`${API_BASE_URL}/resumes/${resumeId}/match`, { method: 'POST' }).then((response) =>
    readJson<MatchResult[]>(response),
  )
}

export function fetchStoredMatches(resumeId: number): Promise<MatchResult[]> {
  return fetch(`${API_BASE_URL}/resumes/${resumeId}/matches`).then((response) =>
    readJson<MatchResult[]>(response),
  )
}
