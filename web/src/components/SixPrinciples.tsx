import type { PrincipleAxis } from '../api/client'

/** 0414 §7.3.1 6대 원칙 축 — 자동 진단이 닿지 않는 축은 note로 체크리스트를 안내한다. */
export default function SixPrinciples({ axes }: { axes: PrincipleAxis[] }) {
  return (
    <div className="principles">
      {axes.map((a) => (
        <div key={a.principle} className="principle">
          <div className="principle-name">{a.principle}</div>
          <div className={`principle-count${a.finding_count > 0 ? ' hit' : ''}`}>
            {a.rules.length > 0 ? `${a.finding_count}건` : '—'}
          </div>
          {a.note && <div className="principle-note">{a.note}</div>}
        </div>
      ))}
    </div>
  )
}
