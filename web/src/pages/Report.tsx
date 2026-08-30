import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  ApiError,
  getChecklist,
  getReport,
  getSbom,
  getScan,
  rescan,
} from '../api/client'
import type {
  Checklist,
  EasyReport,
  Report as DevReport,
  SbomResponse,
  ScanStatus,
} from '../api/client'
import CopyButton from '../components/CopyButton'
import DiffPanel from '../components/DiffPanel'
import FindingCard from '../components/FindingCard'
import GradePill from '../components/GradePill'
import PublishFlow from '../components/PublishFlow'
import SixPrinciples from '../components/SixPrinciples'
import UpgradeBlock from '../components/UpgradeBlock'

type Tab = '발견 사항' | 'SBOM' | '체크리스트' | '공급망'
const TABS: Tab[] = ['발견 사항', 'SBOM', '체크리스트', '공급망']

export default function Report() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [report, setReport] = useState<DevReport | null>(null)
  const [easyReport, setEasyReport] = useState<EasyReport | null>(null)
  const [scan, setScan] = useState<ScanStatus | null>(null)
  const [sbom, setSbom] = useState<SbomResponse | null>(null)
  const [checklist, setChecklist] = useState<Checklist | null>(null)
  const [tab, setTab] = useState<Tab>('발견 사항')
  const [easy, setEasy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [rescanBusy, setRescanBusy] = useState(false)
  const rescanFile = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!id) return
    let cancelled = false
    Promise.all([getReport(id, 'dev'), getReport(id, 'easy'), getScan(id)])
      .then(([dev, ez, s]) => {
        if (cancelled) return
        setReport(dev)
        setEasyReport(ez)
        setScan(s)
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof ApiError ? e.detail : String(e))
      })
    return () => {
      cancelled = true
    }
  }, [id])

  useEffect(() => {
    if (!id) return
    if (tab === 'SBOM' && !sbom) getSbom(id).then(setSbom).catch(() => {})
    if (tab === '체크리스트' && !checklist) getChecklist(id).then(setChecklist).catch(() => {})
  }, [tab, id, sbom, checklist])

  async function doRescan(file?: File) {
    if (!id) return
    setRescanBusy(true)
    try {
      const { scan_id } = await rescan(id, file)
      navigate(`/scan/${scan_id}`)
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : String(e))
      setRescanBusy(false)
    }
  }

  function downloadSbomJson() {
    if (!id) return
    const save = (data: SbomResponse) => {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `ansimcode-sbom-${id}.json`
      a.click()
      URL.revokeObjectURL(a.href)
    }
    if (sbom) save(sbom)
    else
      getSbom(id)
        .then((d) => {
          setSbom(d)
          save(d)
        })
        .catch(() => {})
  }

  if (error) {
    return (
      <div>
        <div className="banner-error" role="alert">{error}</div>
        <p>
          <Link to="/">처음으로</Link>
        </p>
      </div>
    )
  }
  if (!report) return <p className="report-loading" role="status">리포트를 불러오는 중…</p>

  return (
    <div className="report-page">
      <header className="page-heading report-title">
        <p className="page-eyebrow">SECURITY REPORT</p>
        <h1>소스코드 안전 진단 결과</h1>
        <p>발견 사항의 근거와 개선 방법, 소프트웨어 구성요소를 한눈에 확인하세요.</p>
      </header>
      {/* 상단 고정 영역 — 등급·면책·상향·토글·복사·재진단 */}
      <section className="card report-head" aria-label="진단 결과 요약">
        <div className="report-head-row">
          <GradePill grade={report.grade} big />
          <div className="report-head-actions">
            <label className="easy-toggle">
              <input type="checkbox" checked={easy} onChange={(e) => setEasy(e.target.checked)} />
              시민용(쉬운 설명)
            </label>
            {report.copy_all_fix_prompts && (
              <CopyButton text={report.copy_all_fix_prompts} label="전체 수정 프롬프트 복사" />
            )}
            {scan?.source_type === 'zip' ? (
              <>
                <button
                  type="button"
                  className="ghost"
                  disabled={rescanBusy}
                  onClick={() => rescanFile.current?.click()}
                >
                  {rescanBusy ? '재진단 시작 중…' : '재진단 (수정 zip 업로드)'}
                </button>
                <input
                  ref={rescanFile}
                  type="file"
                  accept=".zip,application/zip"
                  hidden
                  onChange={(e) => {
                    const f = e.target.files?.[0]
                    if (f) void doRescan(f)
                    e.target.value = ''
                  }}
                />
              </>
            ) : (
              <button
                type="button"
                className="ghost"
                disabled={rescanBusy}
                onClick={() => void doRescan()}
              >
                {rescanBusy ? '재진단 시작 중…' : '재진단'}
              </button>
            )}
            {id && scan && <PublishFlow scanId={id} sourceType={scan.source_type} />}
          </div>
        </div>

        <p className="disclaimer-strip">{report.disclaimer}</p>
        {report.review_needed_count > 0 && (
          <p className="review-strip">
            AI 검토가 필요한 항목 <b>{report.review_needed_count}건</b>이 포함되어 있습니다 — 등급에는
            반영되지 않습니다.
          </p>
        )}
        {report.provenance.vuln_match_incomplete && (
          <p className="review-strip">취약점 DB 대조가 일부 완료되지 않았습니다(부분 결과).</p>
        )}
        {report.provenance.registry_lookup_incomplete && (
          <p className="review-strip">
            레지스트리 메타데이터가 일부 조회되지 않았습니다 — 장기 미갱신·라이선스 판정이
            불완전할 수 있습니다.
          </p>
        )}
        {report.upgrade && <UpgradeBlock data={report.upgrade} />}
      </section>

      {scan?.previous_comparison && <DiffPanel comparison={scan.previous_comparison} />}

      <section className="card principles-card" aria-labelledby="principles-title">
        <div className="section-heading">
          <span>01</span>
          <h2 id="principles-title">개인정보보호 6대 원칙 축</h2>
        </div>
        <SixPrinciples axes={report.six_principles} />
      </section>

      <div className="tabs" role="tablist" aria-label="진단 결과 상세">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            role="tab"
            aria-selected={tab === t}
            className={`tab${tab === t ? ' active' : ''}`}
            onClick={() => setTab(t)}
          >
            {t}
            {t === '발견 사항' && ` (${report.findings.length})`}
            {t === 'SBOM' && ` (${report.sbom_summary.component_count})`}
          </button>
        ))}
      </div>

      {tab === '발견 사항' && (
        <div className="tab-panel" role="tabpanel">
          {easy && easyReport && (
            <div className="card">
              <h2>쉬운 설명 요약</h2>
              {easyReport.easy_descriptions.length === 0 ? (
                <p className="sub">쉬운 설명이 준비된 항목이 없습니다.</p>
              ) : (
                <ul>
                  {easyReport.easy_descriptions.map((d, i) => (
                    <li key={i}>{d}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
          {report.findings.length === 0 ? (
            <div className="card">발견된 사항이 없습니다.</div>
          ) : (
            report.findings.map((f) => <FindingCard key={f.id} finding={f} easy={easy} />)
          )}
        </div>
      )}

      {tab === 'SBOM' && (
        <div className="card tab-panel" role="tabpanel">
          <div className="report-head-row">
            <h2>
              SBOM — 컴포넌트 {report.sbom_summary.component_count}개 · 취약{' '}
              {report.sbom_summary.vulnerable_count}개
            </h2>
            <button type="button" className="ghost" onClick={downloadSbomJson}>
              JSON 다운로드
            </button>
          </div>
          {!sbom ? (
            <p className="sub">불러오는 중…</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>컴포넌트</th>
                    <th>버전</th>
                    <th>생태계</th>
                    <th>관계</th>
                    <th>라이선스</th>
                    <th>결합형태</th>
                    <th>CVE</th>
                    <th>CVSS</th>
                    <th>심각도</th>
                  </tr>
                </thead>
                <tbody>
                  {sbom.components.map((c) => (
                    <tr key={c.unique_id}>
                      <td title={c.unique_id}>{c.component_name}</td>
                      <td>{c.version ?? '—'}</td>
                      <td>{c.ecosystem}</td>
                      <td>{c.relationship ?? '—'}</td>
                      <td>{c.license_name ?? '불명'}</td>
                      <td>{c.license_usage ?? '—'}</td>
                      <td>{c.cve_ids?.length ? c.cve_ids.join(', ') : '—'}</td>
                      <td>{c.cvss_base ?? (c.cvss_null_reason ? `— (${c.cvss_null_reason})` : '—')}</td>
                      <td>{c.cvss_severity ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === '체크리스트' && (
        <div className="card tab-panel" role="tabpanel">
          <h2>조직 요구사항 통합 체크리스트</h2>
          {!checklist ? (
            <p className="sub">불러오는 중…</p>
          ) : (
            <>
              <p className="sub">{checklist.disclaimer}</p>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>번호</th>
                      <th>분류</th>
                      <th>점검 항목</th>
                      <th>근거 조항</th>
                    </tr>
                  </thead>
                  <tbody>
                    {checklist.items.map((it) => (
                      <tr key={it.id}>
                        <td>{it.id}</td>
                        <td>{it.category}</td>
                        <td>{it.question}</td>
                        <td>{it.standard_ref}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      {tab === '공급망' && (
        <div className="card tab-panel" role="tabpanel">
          <h2>공급망 환경 분류</h2>
          <p>
            분류: <b>{report.supply_chain.class ?? '미분류'}</b>
            {report.supply_chain.matrix.standard_ref && (
              <span className="clause-badge"> {report.supply_chain.matrix.standard_ref}</span>
            )}
          </p>
          {report.supply_chain.matrix.risk_factors.length === 0 ? (
            <p className="sub">식별된 위험요인이 없습니다.</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>위험요인</th>
                    <th>해당 컴포넌트 수</th>
                  </tr>
                </thead>
                <tbody>
                  {report.supply_chain.matrix.risk_factors.map((r) => (
                    <tr key={r.name}>
                      <td>{r.name}</td>
                      <td>{r.component_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <p className="disclaimer-line">{report.disclaimer}</p>
    </div>
  )
}
