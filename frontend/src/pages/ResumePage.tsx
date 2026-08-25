import { useEffect, useRef, useState } from 'react'
import type { DragEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { fetchResumeSkills, startMatching, uploadResume } from '../api/resumes'
import { usePageView } from '../hooks/usePageView'
import { logEvent } from '../utils/logEvent'
import { getCurrentResumeId, setCurrentResumeId } from '../utils/resumeSession'
import type { MemberSkill } from '../types/resume'

type Status = 'idle' | 'checking' | 'uploading' | 'ready' | 'matching' | 'error'

function Spinner() {
  return <span className="spinner" aria-label="처리 중" />
}

const ACCEPTED_EXTENSIONS = ['.pdf', '.txt', '.md', '.xlsx', '.docx']

function hasAcceptedExtension(filename: string) {
  const lower = filename.toLowerCase()
  return ACCEPTED_EXTENSIONS.some((ext) => lower.endsWith(ext))
}

export default function ResumePage() {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [status, setStatus] = useState<Status>('checking')
  const [error, setError] = useState<string | null>(null)
  const [resumeId, setResumeId] = useState<number | null>(null)
  const [skills, setSkills] = useState<MemberSkill[]>([])
  const [dragOver, setDragOver] = useState(false)
  const [uploadingNames, setUploadingNames] = useState<string[]>([])
  const [pastedText, setPastedText] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  usePageView('resume_page_view', { has_existing_resume: getCurrentResumeId() !== null })

  useEffect(() => {
    const current = getCurrentResumeId()
    if (current === null) {
      setStatus('idle')
      return
    }
    fetchResumeSkills(current)
      .then((existingSkills) => {
        setResumeId(current)
        setSkills(existingSkills)
        setStatus('ready')
      })
      .catch(() => setStatus('idle'))
  }, [])

  async function handleFiles(files: File[]) {
    const rejected = files.filter((file) => !hasAcceptedExtension(file.name))
    if (rejected.length > 0) {
      setStatus('error')
      setError(`지원하지 않는 파일 형식입니다: ${rejected.map((file) => file.name).join(', ')}`)
      return
    }
    setUploadingNames(files.map((file) => file.name))
    setStatus('uploading')
    setError(null)
    const fileTypes = [...new Set(files.map((file) => file.name.split('.').pop() ?? ''))]
    void logEvent('resume_upload_submit', { file_count: files.length, file_types: fileTypes })
    try {
      const result = await uploadResume(files, title)
      setCurrentResumeId(result.id)
      setResumeId(result.id)
      setSkills(result.skills)
      setStatus('ready')
      void logEvent('resume_upload_success', { file_count: files.length, file_types: fileTypes }, { resumeId: result.id })
    } catch (reason) {
      setStatus('error')
      const message = reason instanceof Error ? reason.message : '업로드에 실패했습니다.'
      setError(message)
      void logEvent('resume_upload_error', { file_count: files.length, file_types: fileTypes, message })
    }
  }

  async function handleMatch() {
    if (!resumeId) return
    setStatus('matching')
    setError(null)
    void logEvent('match_start_click', {}, { resumeId })
    try {
      const matches = await startMatching(resumeId)
      void logEvent('match_start_success', { match_count: matches.length }, { resumeId })
      navigate(`/match/${resumeId}`)
    } catch (reason) {
      setStatus('error')
      setError(reason instanceof Error ? reason.message : '매칭에 실패했습니다.')
    }
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setDragOver(false)
    const files = Array.from(event.dataTransfer.files)
    if (files.length > 0) void handleFiles(files)
  }

  async function handlePastedTextSubmit() {
    const trimmed = pastedText.trim()
    if (!trimmed) return
    const file = new File([trimmed], '붙여넣은 텍스트.txt', { type: 'text/plain' })
    await handleFiles([file])
    setPastedText('')
  }

  return (
    <main className="page-shell">
      <Link className="back-link" to="/">← 공고 목록</Link>
      <header className="page-header">
        <div>
          <p className="eyebrow">RESUME</p>
          <h1>이력서, 포트폴리오, 경험정리를 올리면<br /><em>AI가 역량을 정리해드려요.</em></h1>
          <p className="header-copy">PDF·워드·엑셀·텍스트 파일을 올리거나(여러 개 동시 가능) 텍스트를 직접 붙여넣으면, 역량을 추출하고 등록된 공고와 매칭해드립니다.</p>
        </div>
      </header>

      {status === 'ready' && (
        <p className="session-notice">현재 이 브라우저 세션에 등록된 이력서를 사용 중입니다. 아래에서 새로 올리거나 붙여넣으면 교체됩니다.</p>
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
          accept=".pdf,.txt,.md,.xlsx,.docx"
          multiple
          hidden
          onChange={(event) => {
            const files = Array.from(event.target.files ?? [])
            if (files.length > 0) void handleFiles(files)
            event.target.value = ''
          }}
        />
        {status === 'uploading' ? (
          <>
            <Spinner />
            <span>{uploadingNames.join(', ')} 분석 중입니다...</span>
          </>
        ) : (
          <>
            <strong>파일을 여기로 끌어다 놓거나 클릭해서 선택하세요. (여러 개 선택 가능)</strong>
            <span className="muted">이력서 · 포트폴리오 (PDF/TXT/MD/XLSX/DOCX, 파일당 최대 10MB, 최대 5개)</span>
          </>
        )}
      </section>

      <div className="or-divider"><span>또는</span></div>

      <section className="paste-text-block">
        <textarea
          className="paste-textarea"
          placeholder="이력서·포트폴리오 내용을 여기에 텍스트로 바로 붙여넣으세요."
          value={pastedText}
          onChange={(event) => setPastedText(event.target.value)}
          rows={8}
          disabled={status === 'uploading'}
        />
        <button
          type="button"
          className="secondary-button"
          disabled={!pastedText.trim() || status === 'uploading'}
          onClick={() => void handlePastedTextSubmit()}
        >
          텍스트로 등록
        </button>
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
