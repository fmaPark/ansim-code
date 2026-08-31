import { useEffect, useState } from 'react'
import type { CSSProperties } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { pollScan } from '../api/client'
import type { ScanStatus, Stage } from '../api/client'

// 0259 §11 5단계 용어 그대로 (G12)
const STAGES: Stage[] = ['환경분석', '현황진단', '위험분석', '대책수립', '완료']

export default function ScanProgress() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [state, setState] = useState<ScanStatus | null>(null)
  const [pollError, setPollError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    let cancelled = false
    pollScan(id, setState, () => cancelled)
      .then((final) => {
        if (final?.status === 'done') navigate(`/report/${id}`)
      })
      .catch((e) => {
        if (!cancelled) setPollError(String(e instanceof Error ? e.message : e))
      })
    return () => {
      cancelled = true
    }
  }, [id, navigate])

  const stageIdx = state?.current_stage ? STAGES.indexOf(state.current_stage) : -1
  const progress = stageIdx >= 0 ? Math.round(((stageIdx + 1) / STAGES.length) * 100) : 0
  const statusLabel = state?.status === 'running' ? '분석 중' : state?.status === 'queued' ? '대기 중' : state?.status ?? '대기 중'
  const progressMessage = state?.current_stage
    ? `${state.current_stage}을 진행하고 있습니다`
    : '진단을 준비하고 있습니다'

  return (
    <div className="progress-page">
      <header className="page-heading progress-heading">
        <h1>진단 진행 중</h1>
        <p>일반 규모 저장소는 2분 이내에 완료됩니다.</p>
      </header>

      <section className="progress-card" aria-labelledby="progress-card-title">
        <div
          className="progress-ring"
          role="progressbar"
          aria-label="전체 진단 진행률"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={progress}
          style={{ '--progress': `${progress}%` } as CSSProperties}
        >
          <div className="progress-ring__inner">
            <h2 id="progress-card-title">{progressMessage}</h2>
            <span className="progress-state">{statusLabel}</span>
          </div>
        </div>

        <p className="progress-callout" role="status" aria-live="polite">
          <span className="progress-callout__dot" aria-hidden="true" />
          {progressMessage}
          <span className="sr-only"> — 상태: {statusLabel}</span>
        </p>

        <div className="stepper" aria-label="진단 진행 단계">
          {STAGES.map((s, i) => (
            <div
              key={s}
              className={`step${i < stageIdx ? ' done' : ''}${i === stageIdx ? ' active' : ''}`}
              aria-current={i === stageIdx ? 'step' : undefined}
            >
              <span className="step__number" aria-hidden="true">{i < stageIdx ? '✓' : i + 1}</span>
              <span className="step__label">{s}</span>
            </div>
          ))}
        </div>

        {state?.status === 'failed' ? (
          <div>
            <div className="banner-error" role="alert">
              진단에 실패했습니다.
              {state.error_message ? `\n${state.error_message}` : ''}
            </div>
            <p>
              <Link to="/">처음으로 돌아가기</Link>
            </p>
          </div>
        ) : pollError ? (
          <div className="banner-error" role="alert">상태 조회에 실패했습니다: {pollError}</div>
        ) : null}
        <p className="progress-note">원본 소스코드는 진단 완료 후 즉시 파기됩니다.</p>
      </section>
    </div>
  )
}
