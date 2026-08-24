export interface MatchedPoint {
  applicant_capability: string
  jd_requirement: string
  explanation: string
  strength: 'high' | 'medium' | 'low' | string
}

export interface GapPoint {
  jd_requirement: string
  current_state: string
  suggestion: string
}

export interface MatchAnalysis {
  resume_id: number
  role_id: number
  ai_match_score: number | null
  score_reason: string | null
  matched_points: MatchedPoint[]
  gap_points: GapPoint[]
  summary: string | null
  recommended_emphasis: string[]
}
