// AnsimCode API 클라이언트 — 백엔드 계약(Task 19 report/builder.py·schemas.py)과 1:1 타입.
// 경로는 상대 /api/* — nginx가 api:8000으로 프록시한다(개발 시 vite proxy).

export type Grade = '안심' | '주의' | '위험'
export type ScanState = 'queued' | 'running' | 'done' | 'failed'
export type Stage = '환경분석' | '현황진단' | '위험분석' | '대책수립' | '완료'
export type Severity = 'critical' | 'high' | 'medium' | 'low'
export type FindingStatus = 'confirmed' | 'review_needed'

export interface DiffEntry {
  id: number | null
  rule_id: string
  file_path: string | null
  line: number | null
  severity: string
  status: FindingStatus
}

export interface PreviousComparison {
  previous_grade: string | null
  grade: string | null
  fingerprint_changed: boolean
  diff: {
    resolved_count: number
    remaining_count: number
    new_count: number
    resolved: DiffEntry[]
    remaining: DiffEntry[]
    new: DiffEntry[]
  }
}

export interface ScanStatus {
  status: ScanState
  source_type: 'git' | 'zip'
  current_stage: Stage | null
  grade: Grade | null
  error_message: string | null
  previous_comparison: PreviousComparison | null
}

export interface Finding {
  id: number
  rule_id: string
  title: string
  standard_ref: string
  severity: Severity
  status: FindingStatus
  grade_blocking: boolean
  file_path: string | null
  line: number | null
  evidence: string | null
  judge_explanation: string | null
  fix_prompt: string | null
  easy_description: string | null
}

export interface UpgradeBlock {
  target: string
  count: number
  message: string
  blocking_finding_ids: number[]
  blocking_cve_ids: string[]
}

export interface PrincipleAxis {
  principle: string
  rules: string[]
  finding_count: number
  note?: string
}

export interface Provenance {
  content_fingerprint: string | null
  fingerprint_type: 'git_commit' | 'tree_hash' | null
  rule_catalog_version: string | null
  llm_model_id: string | null
  vuln_db_snapshot_date: string | null
  vuln_match_incomplete?: boolean
  registry_lookup_incomplete?: boolean
}

export interface RiskFactor {
  name: string
  component_count: number
}

export interface Report {
  grade: Grade
  disclaimer: string
  upgrade: UpgradeBlock | null
  provenance: Provenance
  six_principles: PrincipleAxis[]
  findings: Finding[]
  review_needed_count: number
  sbom_summary: { component_count: number; vulnerable_count: number }
  supply_chain: {
    class: string | null
    matrix: {
      위험요인: string[]
      component_count: number
      standard_ref: string
      risk_factors: RiskFactor[]
    }
  }
  copy_all_fix_prompts: string
}

export interface EasyReport {
  grade: Grade | null
  disclaimer: string
  easy_descriptions: string[]
  review_needed_count: number
}

export interface SbomComponent {
  validation_tool: string
  supplier: string | null
  author: string | null
  component_name: string
  version: string | null
  unique_id: string
  component_hash: string | null
  license_name: string | null
  license_usage: string | null
  vulnerability_db: { id: string; source: string }[] | null
  relationship: 'direct' | 'transitive' | null
  release_date: string | null
  cve_ids: string[] | null
  cvss_base: number | null
  cvss_severity: Severity | null
  cvss_impact: number | null
  cvss_exploitability: number | null
  cvss_null_reason: string | null
  ecosystem: 'pypi' | 'npm'
}

export interface SbomResponse {
  components: SbomComponent[]
  supply_chain_class: string | null
  parse_markers: unknown[]
  generated_by: string
}

export interface ChecklistItem {
  id: string
  standard_ref: string
  category: string
  question: string
}

export interface Checklist {
  items: ChecklistItem[]
  disclaimer: string
}

export interface PublicGrade {
  grade: Grade
  easy_report: EasyReport | null
  provenance: Provenance
  scanned_at: string
  disclaimer: string
}

export interface PublishStep1 {
  token: string
  instructions: string
}

export interface PublishStep2 {
  public_url: string
  badge_markdown: string
}

export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
    this.detail = detail
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init)
  if (!res.ok) {
    let detail = `요청 실패 (HTTP ${res.status})`
    try {
      const body = await res.json()
      if (typeof body?.detail === 'string') detail = body.detail
    } catch {
      /* JSON 아님 — 기본 문구 유지 */
    }
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<T>
}

export function startGitScan(gitUrl: string): Promise<{ scan_id: string }> {
  return req('/api/scans', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ git_url: gitUrl }),
  })
}

export function startZipScan(file: File): Promise<{ scan_id: string }> {
  const form = new FormData()
  form.append('file', file)
  return req('/api/scans', { method: 'POST', body: form })
}

export function getScan(id: string): Promise<ScanStatus> {
  return req(`/api/scans/${id}`)
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

/** 2초 간격 폴링 — done/failed에서 멈춘다. isCancelled로 언마운트 시 중단. */
export async function pollScan(
  id: string,
  onUpdate: (s: ScanStatus) => void,
  isCancelled: () => boolean = () => false,
  intervalMs = 2000,
): Promise<ScanStatus | null> {
  for (;;) {
    if (isCancelled()) return null
    const s = await getScan(id)
    if (isCancelled()) return null
    onUpdate(s)
    if (s.status === 'done' || s.status === 'failed') return s
    await sleep(intervalMs)
  }
}

export function getReport(id: string, mode: 'dev'): Promise<Report>
export function getReport(id: string, mode: 'easy'): Promise<EasyReport>
export function getReport(id: string, mode: 'dev' | 'easy'): Promise<Report | EasyReport> {
  return req(`/api/scans/${id}/report?mode=${mode}`)
}

export function getSbom(id: string): Promise<SbomResponse> {
  return req(`/api/scans/${id}/sbom`)
}

export function getChecklist(id: string): Promise<Checklist> {
  return req(`/api/scans/${id}/checklist`)
}

/** git 재진단은 body 없이, zip은 수정본 재업로드 필수(G1 — 원본은 파기됨). */
export function rescan(id: string, file?: File): Promise<{ scan_id: string }> {
  if (file) {
    const form = new FormData()
    form.append('file', file)
    return req(`/api/scans/${id}/rescan`, { method: 'POST', body: form })
  }
  return req(`/api/scans/${id}/rescan`, { method: 'POST' })
}

export function publish(id: string): Promise<PublishStep1>
export function publish(id: string, confirm: true): Promise<PublishStep2>
export function publish(id: string, confirm?: true): Promise<PublishStep1 | PublishStep2> {
  return req(`/api/scans/${id}/publish`, {
    method: 'POST',
    ...(confirm
      ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ confirm: true }) }
      : {}),
  })
}

export function getPublicGrade(slug: string): Promise<PublicGrade> {
  return req(`/api/public/grades/${slug}`)
}
