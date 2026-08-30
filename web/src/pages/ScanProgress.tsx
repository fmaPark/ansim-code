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
    <div>
      <h1>진단 진행 중</h1>
      <p className="sub">일반 규모 저장소는 2분 이내에 완료됩니다.</p>

      <div className="card">
        <div className="stepper">
          {STAGES.map((s, i) => (
            <div
              key={s}
              className={`step${i < stageIdx ? ' done' : ''}${i === stageIdx ? ' active' : ''}`}
            >
              {s}
            </div>
          ))}
        </div>

        {state?.status === 'failed' ? (
          <div>
            <div className="banner-error">
              진단에 실패했습니다.
              {state.error_message ? `\n${state.error_message}` : ''}
            </div>
            <p>
              <Link to="/">처음으로 돌아가기</Link>
            </p>
          </div>
        ) : pollError ? (
          <div className="banner-error">상태 조회에 실패했습니다: {pollError}</div>
        ) : (
          <p>
            <span className="spinner" />
            {state?.current_stage ?? '대기 중'} — 상태: {state?.status ?? 'queued'}
          </p>
        )}
      </div>
    </div>
  )
}
