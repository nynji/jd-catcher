export interface MatchResult {
  application_id: number | null
  role_id: number
  role_name: string | null
  posting_id: number
  company: string
  title: string | null
  deadline: string | null
  linkareer_url: string
  apply_url: string | null
  match_score: number
}

export interface ExplainResult {
  application_id: number
  explanation: string
}
