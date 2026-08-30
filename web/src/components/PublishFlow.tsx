import { useEffect, useRef, useState } from 'react'
import { ApiError, publish } from '../api/client'
import type { PublishStep1, PublishStep2 } from '../api/client'
import CopyButton from './CopyButton'
import ActionButton from './ui/ActionButton'

// 서버 public.py의 ZIP_PUBLISH_NOTICE(§11 항목 8 placeholder)와 동일 문구 —
// 비활성 버튼은 서버를 호출하지 않으므로 여기 미러링한다(직접 API 호출은 403 + 이 문구).
const ZIP_PUBLISH_NOTICE =
  'zip 업로드 진단은 소유 증명이 불가능해 등급 공개를 지원하지 않습니다. ' +
  '공개가 필요하면 공개 git 저장소 URL로 다시 진단해 주세요.'

export default function PublishFlow({ scanId, sourceType }: { scanId: string; sourceType: 'git' | 'zip' }) {
  const [open, setOpen] = useState(false)
  const [step1, setStep1] = useState<PublishStep1 | null>(null)
  const [step2, setStep2] = useState<PublishStep2 | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const modalRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (open) closeButtonRef.current?.focus()
  }, [open])

  function close() {
    setOpen(false)
    triggerRef.current?.focus()
  }

  function handleDialogKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (e.key === 'Escape') {
      e.preventDefault()
      close()
      return
    }
    if (e.key !== 'Tab') return
    const focusable = Array.from(
      modalRef.current?.querySelectorAll<HTMLElement>(
        'button:not([disabled]), a[href], input:not([disabled]), [tabindex]:not([tabindex="-1"])',
      ) ?? [],
    )
    if (focusable.length === 0) return
    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault()
      last.focus()
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault()
      first.focus()
    }
  }

  if (sourceType === 'zip') {
    return (
      <span className="publish-zip-wrap" title={ZIP_PUBLISH_NOTICE}>
        <button type="button" className="ghost" disabled>
          공개하기 (zip 미지원)
        </button>
      </span>
    )
  }

  async function start() {
    setOpen(true)
    setError(null)
    if (step1) return // 이미 발급된 토큰 유지 — 재발급하면 커밋해 둔 토큰이 무효가 된다
    setBusy(true)
    try {
      setStep1(await publish(scanId))
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : String(e))
    } finally {
      setBusy(false)
    }
  }

  async function confirm() {
    setBusy(true)
    setError(null)
    try {
      setStep2(await publish(scanId, true))
    } catch (e) {
      // 409: .ansimcode 불일치 — 재안내 후 같은 토큰으로 다시 확인 가능
      setError(e instanceof ApiError ? e.detail : String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <ActionButton ref={triggerRef} type="button" onClick={() => void start()}>
        공개하기
      </ActionButton>
      {open && (
        <div className="modal-backdrop" onMouseDown={close}>
          <div
            ref={modalRef}
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="publish-dialog-title"
            onKeyDown={handleDialogKeyDown}
            onMouseDown={(e) => e.stopPropagation()}
          >
            <div className="modal-head">
              <h2 id="publish-dialog-title">등급 공개 — 저장소 소유 증명</h2>
              <button ref={closeButtonRef} type="button" className="ghost" onClick={close}>
                닫기 ✕
              </button>
            </div>

            {step2 ? (
              <div>
                <p className="publish-success">공개가 완료되었습니다 🎉</p>
                <div className="publish-row">
                  <span>
                    공개 페이지: <a href={step2.public_url}>{step2.public_url}</a>
                  </span>
                  <CopyButton text={new URL(step2.public_url, location.origin).href} label="URL 복사" />
                </div>
                <p>README에 붙일 배지 마크다운:</p>
                <pre className="badge-markdown">
                  <code>{step2.badge_markdown}</code>
                </pre>
                <CopyButton text={step2.badge_markdown} label="배지 마크다운 복사" />
              </div>
            ) : (
              <div>
                <ol className="publish-steps">
                  <li className={step1 ? 'done' : ''}>일회용 토큰 발급</li>
                  <li>
                    저장소 <b>루트에 <code>.ansimcode</code> 파일</b>을 만들어 토큰 한 줄을 커밋·푸시
                  </li>
                  <li>아래 [커밋했어요, 확인]을 눌러 소유 증명</li>
                </ol>
                {busy && !step1 && <p className="sub">토큰 발급 중…</p>}
                {step1 && (
                  <>
                    <div className="publish-row">
                      <pre className="token-box">
                        <code>{step1.token}</code>
                      </pre>
                      <CopyButton text={step1.token} label="토큰 복사" />
                    </div>
                    <p className="sub">{step1.instructions}</p>
                    <ActionButton type="button" loading={busy} disabled={busy} onClick={() => void confirm()}>
                      {busy ? '저장소 확인 중…' : '커밋했어요, 확인'}
                    </ActionButton>
                  </>
                )}
                {error && <div className="banner-error" role="alert">{error}</div>}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
