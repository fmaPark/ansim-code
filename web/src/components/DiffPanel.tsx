import type { DiffEntry, PreviousComparison } from '../api/client'
import GradePill from './GradePill'

function DiffList({ title, entries, tone }: { title: string; entries: DiffEntry[]; tone: string }) {
  return (
    <div className={`diff-col diff-${tone}`}>
      <div className="diff-col-head">
        {title} <b>{entries.length}</b>
      </div>
      {entries.length === 0 ? (
        <div className="diff-empty">없음</div>
      ) : (
        <ul>
          {entries.map((e, i) => (
            <li key={e.id ?? `${e.rule_id}-${i}`}>
              <code>{e.rule_id}</code>{' '}
              {e.file_path ? `${e.file_path}${e.line ? `:${e.line}` : ''}` : '저장소 전체'}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

/** 재진단 비교 — "해결 N · 잔여 M · 신규 K" (TDD §4.7 유스케이스 3). */
export default function DiffPanel({ comparison: c }: { comparison: PreviousComparison }) {
  return (
    <div className="card diff-panel">
      <h2>재진단 비교</h2>
      <p className="diff-grade-change">
        <GradePill grade={c.previous_grade} /> <span className="arrow">→</span>{' '}
        <GradePill grade={c.grade} />
        {!c.fingerprint_changed && (
          <span className="fingerprint-note">코드 변경 없음 (콘텐츠 지문 동일)</span>
        )}
      </p>
      <div className="diff-grid">
        <DiffList title="해결" entries={c.diff.resolved} tone="resolved" />
        <DiffList title="잔여" entries={c.diff.remaining} tone="remaining" />
        <DiffList title="신규" entries={c.diff.new} tone="new" />
      </div>
    </div>
  )
}
