import { useState } from 'react'
import type { Finding } from '../api/client'
import CopyButton from './CopyButton'

function location(f: Finding): string {
  if (!f.file_path) return '저장소 전체'
  return f.line ? `${f.file_path}:${f.line}` : f.file_path
}

export default function FindingCard({ finding: f, easy }: { finding: Finding; easy: boolean }) {
  const [showFix, setShowFix] = useState(false)
  const fixId = `finding-${f.id}-fix`

  return (
    <div id={`finding-${f.id}`} className={`finding${f.grade_blocking ? ' blocking' : ''}`}>
      <div className="finding-head">
        <span className={`sev sev-${f.severity}`}>{f.severity}</span>
        <strong>
          {f.rule_id} · {f.title}
        </strong>
        <span className="clause-badge" title="근거 조항">
          {f.standard_ref}
        </span>
        {f.status === 'review_needed' ? (
          <span className="status-badge review">검토 필요</span>
        ) : (
          <span className="status-badge confirmed">확정</span>
        )}
        {f.grade_blocking && <span className="status-badge blocking-badge">등급 차단</span>}
      </div>

      <div className="finding-loc">{location(f)}</div>

      {easy ? (
        <p className="easy-desc">{f.easy_description ?? '시민용 설명이 없는 항목입니다.'}</p>
      ) : (
        <>
          {f.evidence && (
            <pre className="evidence">
              <code>{f.evidence}</code>
            </pre>
          )}
          {f.judge_explanation && <p className="judge-note">AI 판정 참고: {f.judge_explanation}</p>}
          {f.fix_prompt && (
            <div className="fix-block">
              <button
                type="button"
                className="ghost"
                aria-expanded={showFix}
                aria-controls={fixId}
                onClick={() => setShowFix((v) => !v)}
              >
                {showFix ? '수정 프롬프트 접기 ▲' : '수정 프롬프트 보기 ▼'}
              </button>
              {showFix && (
                <div className="fix-body" id={fixId}>
                  <pre>
                    <code>{f.fix_prompt}</code>
                  </pre>
                  <CopyButton text={f.fix_prompt} label="프롬프트 복사" />
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
