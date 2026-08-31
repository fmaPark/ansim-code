import type { ReactNode } from 'react'

export interface ReportTableFrameProps {
  title: string
  count?: number
  ariaLabel: string
  action?: ReactNode
  children: ReactNode
  scrollHint?: boolean
  variant?: 'finding' | 'dense'
}

export default function ReportTableFrame({
  title,
  count,
  ariaLabel,
  action,
  children,
  scrollHint = false,
  variant = 'dense',
}: ReportTableFrameProps) {
  return (
    <section
      className={`report-table-frame report-table-frame--${variant}`}
      aria-label={ariaLabel}
    >
      <header className="report-table-frame__header">
        <h2>
          {title}
          {typeof count === 'number' && <span className="report-table-count">{count}</span>}
        </h2>
        {action && <div className="report-table-actions">{action}</div>}
      </header>
      {scrollHint && <p className="report-table-scroll-hint">표를 좌우로 스크롤해 전체 항목을 확인하세요.</p>}
      <div className="report-table-scroll">{children}</div>
    </section>
  )
}
