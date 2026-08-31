import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError, startGitScan, startZipScan } from '../api/client'
import ActionButton from '../components/ui/ActionButton'

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
    <div className="home-page">
      <section className="home-hero" aria-labelledby="home-title">
        <h1 id="home-title">소스코드 안전 자가진단</h1>
        <p className="home-lead">
          TTA 표준 4종 기반 진단 룰 31종 · 15속성 SBOM · 안전등급을 제공합니다.
        </p>
      </section>

      <section className="home-card" aria-labelledby="git-scan-title">
        <div className="home-card__heading">
          <div>
            <h2 id="git-scan-title">공개 git 저장소</h2>
          </div>
        </div>
        <form className="git-form" onSubmit={submitGit}>
          <input
            aria-label="공개 git 저장소"
            type="url"
            placeholder="https://github.com/owner/repo"
            value={gitUrl}
            onChange={(e) => setGitUrl(e.target.value)}
            disabled={busy}
          />
          <ActionButton className="primary-action" type="submit" size="large" loading={busy} disabled={busy || !gitUrl.trim()}>
            {busy ? '시작 중…' : '진단 시작'}
          </ActionButton>
        </form>
      </section>

      <section className="home-card" aria-labelledby="zip-scan-title">
        <div className="home-card__heading">
          <div>
            <h2 id="zip-scan-title">zip 파일로 진단</h2>
          </div>
        </div>
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
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              fileInput.current?.click()
            }
          }}
          role="button"
          aria-label="zip 파일 업로드"
          tabIndex={busy ? -1 : 0}
        >
          <svg className="dropzone__icon" aria-hidden="true" viewBox="0 0 24 24">
            <path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M5 14v4.5A1.5 1.5 0 006.5 20h11a1.5 1.5 0 001.5-1.5V14" />
          </svg>
          <strong>zip 파일을 끌어다 놓거나 선택해 주세요</strong>
          <div>50MB 이하 · 진단 후 원본 코드는 즉시 파기됩니다</div>
          <span className="dropzone__select">파일 선택</span>
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
      </section>

      {error && <div className="banner-error" role="alert">{error}</div>}

    </div>
  )
}
