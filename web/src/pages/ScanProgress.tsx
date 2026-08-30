import { useEffect, useState } from 'react'
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

  return (
    <div className="progress-page">
      <header className="page-heading progress-heading">
        <p className="page-eyebrow">SECURITY DIAGNOSIS</p>
        <h1>진단 진행 중</h1>
        <p>소스코드를 안전하게 분석하고 있습니다. 일반 규모 저장소는 2분 이내에 완료됩니다.</p>
      </header>

      <section className="progress-card" aria-labelledby="progress-card-title">
        <div className="progress-card__top">
          <div>
            <span className="progress-kicker">현재 작업</span>
            <h2 id="progress-card-title">{state?.current_stage ?? '진단 준비 중'}</h2>
          </div>
          <span className="progress-state">{state?.status ?? 'queued'}</span>
        </div>
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
        ) : (
          <p className="progress-live" role="status" aria-live="polite">
            <span className="spinner" />
            {state?.current_stage ?? '대기 중'} — 상태: {state?.status ?? 'queued'}
          </p>
        )}
        <p className="progress-note">창을 닫지 않아도 진단이 완료되면 결과 화면으로 자동 이동합니다.</p>
      </section>
    </div>
  )
}
