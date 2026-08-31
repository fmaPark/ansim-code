import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, getPublicGrade } from '../api/client'
import type { PublicGrade as PublicGradeData } from '../api/client'
import GradePill from '../components/GradePill'

/** 시민용 공개 페이지 — 큰 등급·쉬운 설명·재현성 앵커·법적 고지 (TDD §4.7 유스케이스 2). */
export default function PublicGrade() {
  const { slug } = useParams<{ slug: string }>()
  const [data, setData] = useState<PublicGradeData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!slug) return
    let cancelled = false
    getPublicGrade(slug)
      .then((d) => {
        if (!cancelled) setData(d)
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof ApiError ? e.detail : String(e))
      })
    return () => {
      cancelled = true
    }
  }, [slug])

  if (error) {
    return (
      <div>
        <div className="banner-error" role="alert">{error}</div>
        <p>
          <Link to="/">안심코드로 직접 진단해 보기</Link>
        </p>
      </div>
    )
  }
  if (!data) return <p className="sub">불러오는 중…</p>

  return (
    <div className="public-grade">
      <header className="public-hero">
        <h1>공개 안전등급</h1>
        <p className="public-owner-note">이 등급은 공개 git 저장소 소유자가 직접 공개했습니다.</p>
        <div className={`public-grade-display public-grade-display--${data.grade}`} aria-label={`안전등급 ${data.grade}`}>
          <span className="public-grade-icon" aria-hidden="true">!</span>
          <GradePill grade={data.grade} big />
        </div>
        <p className="public-date">진단 시각: {new Date(data.scanned_at).toLocaleString('ko-KR')}</p>
      </header>

      <section className="card public-summary" aria-labelledby="easy-summary-title">
        <div className="public-section-title">
          <span aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M5.5 5.5h13v10h-7l-4.5 3v-3H5.5z" />
            </svg>
          </span>
          <h2 id="easy-summary-title">진단 결과 쉬운 설명</h2>
        </div>
        {data.easy_report && data.easy_report.easy_descriptions.length > 0 ? (
          <ul className="public-description-list">
            {data.easy_report.easy_descriptions.map((d, i) => (
              <li key={i}>{d}</li>
            ))}
          </ul>
        ) : (
          <p className="sub">표시할 발견 사항이 없습니다.</p>
        )}
        {data.easy_report && data.easy_report.review_needed_count > 0 && (
          <p className="review-strip">
            AI 검토가 필요한 항목 {data.easy_report.review_needed_count}건은 등급에 반영되지
            않았습니다.
          </p>
        )}
      </section>

      <details className="card provenance">
        <summary>진단 재현성 정보 (콘텐츠 지문·룰 버전·모델·취약점 DB 시점)</summary>
        <table>
          <tbody>
            <tr>
              <th>콘텐츠 지문</th>
              <td>
                <code>{data.provenance.content_fingerprint ?? '—'}</code>{' '}
                {data.provenance.fingerprint_type && `(${data.provenance.fingerprint_type})`}
              </td>
            </tr>
            <tr>
              <th>룰 카탈로그 버전</th>
              <td>
                <code>{data.provenance.rule_catalog_version ?? '—'}</code>
              </td>
            </tr>
            <tr>
              <th>LLM 모델</th>
              <td>
                <code>{data.provenance.llm_model_id ?? '미사용'}</code>
              </td>
            </tr>
            <tr>
              <th>취약점 DB 시점</th>
              <td>
                <code>{data.provenance.vuln_db_snapshot_date ?? '—'}</code>
              </td>
            </tr>
          </tbody>
        </table>
      </details>

      <div className="disclaimer-strip legal">{data.disclaimer}</div>
      <Link className="public-cta" to="/">안심코드로 직접 진단해 보기</Link>
    </div>
  )
}
