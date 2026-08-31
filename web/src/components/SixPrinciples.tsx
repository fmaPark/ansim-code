import type { PrincipleAxis } from '../api/client'

/** 0414 §7.3.1 6대 원칙 축 — 자동 진단이 닿지 않는 축은 note로 체크리스트를 안내한다. */
export default function SixPrinciples({ axes }: { axes: PrincipleAxis[] }) {
  return (
    <div className="principles">
      {axes.map((a) => {
        const status = a.rules.length === 0 ? 'unknown' : a.finding_count > 0 ? 'violation' : 'pass'
        const statusLabel = status === 'pass' ? '준수' : status === 'violation' ? '위반' : '확인 필요'
        return (
          <div key={a.principle} className={`principle principle--${status}`}>
            <div className="principle-name">{a.principle}</div>
            <div className="principle-status">
              <span className="principle-status__icon" aria-hidden="true">
                {status === 'pass' ? '✓' : status === 'violation' ? '!' : '·'}
              </span>
              {statusLabel}
            </div>
            {a.note && <div className="principle-note">{a.note}</div>}
          </div>
        )
      })}
    </div>
  )
}
