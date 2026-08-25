export interface MemberSkill {
  id: number
  skill_name: string
  competency: string
  evidence: string | null
}

export interface ResumeUploadResult {
  id: number
  title: string | null
  skills: MemberSkill[]
}
