export interface MemberSkill {
  id: number
  skill_name: string
  competency: string
  evidence: string | null
}

export interface ResumeSummary {
  id: number
  title: string | null
  created_at: string | null
}

export interface ResumeUploadResult {
  id: number
  title: string | null
  skills: MemberSkill[]
}
