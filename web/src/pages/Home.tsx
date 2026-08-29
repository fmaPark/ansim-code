import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError, startGitScan, startZipScan } from '../api/client'

const MAX_ZIP_BYTES = 50 * 1024 * 1024 // TDD §3 — 서버(G5)와 동일 상한을 클라이언트에서 선검증

export default function Home() {
  const navigate = useNavigate()
  const [gitUrl, setGitUrl] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [drag, setDrag] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)

  async function begin(start: () => Promise<{ scan_id: string }>) {
    setError(null)
    setBusy(true)
    try {
      const { scan_id } = await start()
      navigate(`/scan/${scan_id}`)
    } catch (e) {
      // 서버 detail을 그대로 노출 — "명확한 오류 안내" (ADR §5)
      setError(e instanceof ApiError ? e.detail : `요청에 실패했습니다: ${String(e)}`)
      setBusy(false)
    }
  }

  function submitGit(e: React.FormEvent) {
    e.preventDefault()
    const url = gitUrl.trim()
    if (!url) return
    if (!url.startsWith('https://')) {
      setError('공개 https git URL만 지원합니다')
      return
    }
    void begin(() => startGitScan(url))
  }

  function acceptZip(file: File | undefined | null) {
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.zip')) {
      setError(`zip 파일만 업로드할 수 있습니다 (받은 파일: ${file.name})`)
      return
    }
    if (file.size > MAX_ZIP_BYTES) {
      const mb = (file.size / 1024 / 1024).toFixed(1)
      setError(`zip은 50MB 이하만 지원합니다 (업로드 파일: ${mb}MB)`)
      return
    }
    void begin(() => startZipScan(file))
  }

  return (
    <div>
      <h1>소스코드 안전 자가진단</h1>
      <p className="sub">
        TTA 표준 4종 기반 진단 룰 31종 · 15속성 SBOM · 안전등급(안심·주의·위험)을 제공합니다.
      </p>

      <div className="card">
        <h2>공개 git 저장소로 진단</h2>
        <form className="git-form" onSubmit={submitGit}>
          <input
            type="url"
            placeholder="https://github.com/owner/repo"
            value={gitUrl}
            onChange={(e) => setGitUrl(e.target.value)}
            disabled={busy}
          />
          <button className="primary" type="submit" disabled={busy || !gitUrl.trim()}>
            {busy ? '시작 중…' : '진단 시작'}
          </button>
        </form>
      </div>

      <div className="card">
        <h2>zip 파일로 진단</h2>
        <div
          className={`dropzone${drag ? ' drag' : ''}`}
          onDragOver={(e) => {
            e.preventDefault()
            setDrag(true)
          }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDrag(false)
            acceptZip(e.dataTransfer.files?.[0])
          }}
          onClick={() => fileInput.current?.click()}
          role="button"
          aria-label="zip 파일 업로드"
        >
          <strong>zip 파일을 끌어다 놓거나 클릭해 선택</strong>
          <div>50MB 이하 · 진단 후 원본 코드는 즉시 파기됩니다</div>
          <input
            ref={fileInput}
            type="file"
            accept=".zip,application/zip"
            hidden
            onChange={(e) => {
              acceptZip(e.target.files?.[0])
              e.target.value = ''
            }}
          />
        </div>
      </div>

      {error && <div className="banner-error">{error}</div>}

      <p className="disclaimer-line">본 서비스는 인증이 아닌 자가점검 보조 도구입니다.</p>
    </div>
  )
}
