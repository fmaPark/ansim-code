import { Fragment, useMemo, useState } from 'react'
import type { Finding, FindingStatus, Severity } from '../api/client'
import CopyButton from './CopyButton'
import ReportTableFrame from './ReportTableFrame'

export interface FindingTableProps {
  findings: Finding[]
  easy: boolean
}

type SeverityFilter = 'all' | Severity
type StatusFilter = 'all' | FindingStatus

const severityOptions: Array<{ value: SeverityFilter; label: string }> = [
  { value: 'all', label: '전체 심각도' },
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
]

function location(finding: Finding): string {
  if (!finding.file_path) return '저장소 전체'
  return finding.line ? `${finding.file_path}:${finding.line}` : finding.file_path
}

export default function FindingTable({ findings, easy }: FindingTableProps) {
  const [severity, setSeverity] = useState<SeverityFilter>('all')
  const [status, setStatus] = useState<StatusFilter>('all')
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const filteredFindings = useMemo(
    () =>
      findings.filter(
        (finding) =>
          (severity === 'all' || finding.severity === severity) &&
          (status === 'all' || finding.status === status),
      ),
    [findings, severity, status],
  )

  if (findings.length === 0) {
    return (
      <ReportTableFrame title="발견 사항" count={0} ariaLabel="발견 사항">
        <div className="report-table-empty">발견된 사항이 없습니다.</div>
      </ReportTableFrame>
    )
  }

  const filters = (
    <>
      <span className="report-table-result" aria-live="polite">
        전체 {findings.length}건 중 {filteredFindings.length}건
      </span>
      <label className="report-filter">
        <span className="sr-only">심각도 필터</span>
        <select
          aria-label="심각도 필터"
          value={severity}
          onChange={(event) => {
            setSeverity(event.target.value as SeverityFilter)
            setExpandedId(null)
          }}
        >
          {severityOptions.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      </label>
      <label className="report-filter">
        <span className="sr-only">상태 필터</span>
        <select
          aria-label="상태 필터"
          value={status}
          onChange={(event) => {
            setStatus(event.target.value as StatusFilter)
            setExpandedId(null)
          }}
        >
          <option value="all">전체 상태</option>
          <option value="confirmed">확정</option>
          <option value="review_needed">검토 필요</option>
        </select>
      </label>
    </>
  )

  return (
    <ReportTableFrame
      title="발견 사항"
      count={filteredFindings.length}
      ariaLabel="발견 사항"
      action={filters}
      variant="finding"
    >
      <table className="report-data-table finding-table" aria-label="발견 사항 목록">
        <thead>
          <tr>
            <th scope="col">심각도</th>
            <th scope="col">상태</th>
            <th scope="col">발견 항목</th>
            <th scope="col">위치</th>
            <th scope="col">등급 영향</th>
            <th scope="col"><span className="sr-only">상세</span></th>
          </tr>
        </thead>
        <tbody>
          {filteredFindings.length === 0 ? (
            <tr>
              <td className="report-table-empty-cell" colSpan={6}>
                선택한 조건에 맞는 발견 사항이 없습니다.
              </td>
            </tr>
          ) : filteredFindings.map((finding) => {
            const expanded = expandedId === finding.id
            const detailId = `finding-${finding.id}-detail`
            return (
              <Fragment key={finding.id}>
                <tr
                  id={`finding-${finding.id}`}
                  className={`finding-summary-row${finding.grade_blocking ? ' finding-summary-row--blocking' : ''}`}
                >
                  <td data-label="심각도"><span className={`sev sev-${finding.severity}`}>{finding.severity}</span></td>
                  <td data-label="상태">
                    <span className={`status-badge ${finding.status === 'confirmed' ? 'confirmed' : 'review'}`}>
                      {finding.status === 'confirmed' ? '확정' : '검토 필요'}
                    </span>
                  </td>
                  <td data-label="발견 항목" className="finding-title-cell">
                    <strong>{finding.rule_id} · {finding.title}</strong>
                    <span>발견 #{finding.id} · {finding.standard_ref}</span>
                  </td>
                  <td data-label="위치" className="technical-cell">{location(finding)}</td>
                  <td data-label="등급 영향">
                    {finding.grade_blocking ? (
                      <span className="status-badge blocking-badge">등급 차단</span>
                    ) : (
                      <span className="status-badge neutral">영향 없음</span>
                    )}
                  </td>
                  <td className="finding-toggle-cell">
                    <button
                      type="button"
                      className="finding-detail-toggle"
                      aria-label={`발견 #${finding.id} ${finding.title}, ${location(finding)} 상세`}
                      aria-expanded={expanded}
                      aria-controls={detailId}
                      onClick={() => setExpandedId(expanded ? null : finding.id)}
                    >
                      <span>상세</span>
                      <svg aria-hidden="true" viewBox="0 0 20 20">
                        <path d="m5.5 7.5 4.5 4.5 4.5-4.5" />
                      </svg>
                    </button>
                  </td>
                </tr>
                {expanded && (
                  <tr className="finding-detail-row" id={detailId}>
                    <td colSpan={6}>
                    <div
                      className="finding-detail"
                      role="region"
                      aria-label={`발견 #${finding.id} ${finding.title} 상세`}
                    >
                        {easy ? (
                          <div className="finding-detail-section">
                            <h3>쉬운 설명</h3>
                            <p className="easy-desc">
                              {finding.easy_description ?? '시민용 설명이 없는 항목입니다.'}
                            </p>
                          </div>
                        ) : (
                          <>
                            {finding.evidence && (
                              <div className="finding-detail-section">
                                <h3>근거</h3>
                                <pre className="evidence"><code>{finding.evidence}</code></pre>
                              </div>
                            )}
                            {finding.judge_explanation && (
                              <p className="judge-note">AI 판정 참고: {finding.judge_explanation}</p>
                            )}
                            {finding.fix_prompt && (
                              <div className="finding-detail-section finding-fix">
                                <div className="finding-fix__heading">
                                  <h3>수정 프롬프트</h3>
                                  <CopyButton text={finding.fix_prompt} label="프롬프트 복사" />
                                </div>
                                <pre><code>{finding.fix_prompt}</code></pre>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            )
          })}
        </tbody>
      </table>
    </ReportTableFrame>
  )
}
