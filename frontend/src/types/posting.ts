export type PostingSort = 'deadline' | 'collected_at'

export interface PostingSummary {
  id: number
  company: string
  title: string | null
  job_type: string
  industry: string
  location: string | null
  deadline: string | null
  has_cover_letter: boolean
  linkareer_url: string
  apply_url: string | null
  collected_at: string | null
}

export interface SubmissionRequirement {
  id: number
  posting_id: number
  type: string
  is_required: boolean
  detail: string | null
}

export interface CoverLetterQuestion {
  id: number
  posting_id: number
  role_name: string
  question_text: string
  char_limit: number | null
  question_order: number
}

export interface PostingDetail extends PostingSummary {
  raw_text: string
  is_image_based: boolean
  image_urls: string[]
  submission_requirements: SubmissionRequirement[]
  cover_letter_questions: CoverLetterQuestion[]
}