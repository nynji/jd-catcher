import { useEffect, useRef, useState } from 'react'
import type { DragEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { fetchResumeSkills, fetchResumes, startMatching, uploadResume } from '../api/resumes'
import type { MemberSkill, ResumeSummary } from '../types/resume'

type Status = 'idle' | 'uploading' | 'ready' | 'matching' | 'error'

function Spinner() {
  return <span className="spinner" aria-label="처리 중" />
}

const ACCEPTED_TYPES = ['application/pdf', 'text/plain']

export default function ResumePage() {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [status, setStatus] = useState<Status>('idle')
  const [error, setError] = useState<string | null>(null)
  const [resumeId, setResumeId] = useState<number | null>(null)
  const [skills, setSkills] = useState<MemberSkill[]>([])
  const [resumes, setResumes] = useState<ResumeSummary[]>([])
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    fetchResumes()
      .then(setResumes)
      .catch(() => undefined)
  }, [])

  async function handleFile(file: File) {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      setStatus('error')
      setError('PDF 또는 텍스트 파일만 업로드할 수 있습니다.')
      return
    }
    setStatus('uploading')
    setError(null)
    try {
      const result = await uploadResume(file, title)
      setResumeId(result.id)
      setSkills(result.skills)
      setStatus('ready')
      setResumes((prev) => [{ id: result.id, title: result.title, created_at: null }, ...prev])
    } catch (reason) {
      setStatus('error')
      setError(reason instanceof Error ? reason.message : '업로드에 실패했습니다.')
    }
  }

  async function handleSelectExisting(id: number) {
    setStatus('uploading')
    setError(null)
    try {
      const existingSkills = await fetchResumeSkills(id)
      setResumeId(id)
      setSkills(existingSkills)
      setStatus('ready')
    } catch (reason) {
      setStatus('error')
      setError(reason instanceof Error ? reason.message : '역량을 불러오지 못했습니다.')
    }
  }

  async function handleMatch() {
    if (!resumeId) return
    setStatus('matching')
    setError(null)
    try {
      await startMatching(resumeId)
      navigate(`/match/${resumeId}`)
    } catch (reason) {
      setStatus('error')
      setError(reason instanceof Error ? reason.message : '매칭에 실패했습니다.')
    }
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setDragOver(false)
    const file = event.dataTransfer.files[0]
    if (file) void handleFile(file)
  }

  return (
    <main className="page-shell">
      <Link className="back-link" to="/">← 공고 목록</Link>
      <header className="page-header">
        <div>
          <p className="eyebrow">RESUME</p>
          <h1>이력서를 올리면<br /><em>AI가 역량을 정리해드려요.</em></h1>
          <p className="header-copy">PDF 또는 텍스트 파일을 올리면 역량을 추출하고, 등록된 공고와 매칭해드립니다.</p>
        </div>
      </header>

      {resumes.length > 0 && (
        <section className="toolbar" aria-label="저장된 이력서">
          <span className="section-label">MY RESUMES</span>
          <div className="sort-toggle">
            {resumes.map((resume) => (
              <button
                key={resume.id}
                className={resumeId === resume.id ? 'active' : ''}
                onClick={() => void handleSelectExisting(resume.id)}
              >
                {resume.title || `이력서 #${resume.id}`}
              </button>
            ))}
          </div>
        </section>
      )}

      <input
        className="title-input"
        placeholder="구분명 (예: 네이버 지원용)"
        value={title}
        onChange={(event) => setTitle(event.target.value)}
      />

      <section
        className={`dropzone${dragOver ? ' dragover' : ''}`}
        onDragOver={(event) => {
          event.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => status !== 'uploading' && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,text/plain"
          hidden
          onChange={(event) => {
            const file = event.target.files?.[0]
            if (file) void handleFile(file)
            event.target.value = ''
          }}
        />
        {status === 'uploading' ? (
          <>
            <Spinner />
            <span>AI가 역량을 분석하고 있습니다...</span>
          </>
        ) : (
          <>
            <strong>PDF 또는 텍스트 파일을 여기로 끌어다 놓거나 클릭해서 선택하세요.</strong>
            <span className="muted">이력서 · 포트폴리오 (PDF/TXT, 최대 10MB)</span>
          </>
        )}
      </section>

      {status === 'error' && (
        <div className="state-panel error-panel"><strong>처리할 수 없습니다.</strong><span>{error}</span></div>
      )}

      {skills.length > 0 && (
        <section className="content-section">
          <div className="section-heading"><h2>추출된 역량</h2></div>
          <div className="skill-list">
            {skills.map((skill) => (
              <div className="skill-item" key={skill.id}>
                <div className="skill-head">
                  <strong>{skill.skill_name}</strong>
                  <span className="skill-badge">{skill.competency}</span>
                </div>
                {skill.evidence && <p className="skill-evidence">{skill.evidence}</p>}
              </div>
            ))}
          </div>
          <button className="primary-button" disabled={status === 'matching'} onClick={() => void handleMatch()}>
            {status === 'matching' ? <><Spinner /> 매칭 중...</> : '매칭 시작 →'}
          </button>
        </section>
      )}
    </main>
  )
}
