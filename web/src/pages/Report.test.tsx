import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { EasyReport, Report as ReportData, ScanStatus, SbomResponse } from '../api/client'
import { renderWithRouter } from '../test/render'
import Report from './Report'

const api = vi.hoisted(() => ({
  getChecklist: vi.fn(),
  getReport: vi.fn(),
  getSbom: vi.fn(),
  getScan: vi.fn(),
  rescan: vi.fn(),
  publish: vi.fn(),
}))

vi.mock('../api/client', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api/client')>()
  return { ...actual, ...api }
})

const report: ReportData = {
  grade: '위험',
  disclaimer: '본 결과는 인증이 아닌 자가점검 참고 자료입니다.',
  upgrade: null,
  provenance: {
    content_fingerprint: 'abc123',
    fingerprint_type: 'git_commit',
    rule_catalog_version: 'rules-v1',
    llm_model_id: 'gemini-test',
    vuln_db_snapshot_date: '2026-08-31',
  },
  six_principles: [
    { principle: '목적 제한', rules: ['PII-01'], finding_count: 1 },
    { principle: '최소 수집', rules: ['PII-02'], finding_count: 0 },
    { principle: '정확성', rules: ['PII-03'], finding_count: 0 },
    { principle: '안전성', rules: ['SEC-001'], finding_count: 1 },
    { principle: '보유 기간 제한', rules: [], finding_count: 0, note: '체크리스트 확인' },
    { principle: '접근 제한', rules: ['AUTH-01'], finding_count: 0 },
  ],
  findings: [
    {
      id: 1,
      rule_id: 'SEC-001',
      title: '하드코딩된 비밀정보',
      standard_ref: 'TTAK.KO-12.0259',
      severity: 'high',
      status: 'confirmed',
      grade_blocking: true,
      file_path: 'src/config.ts',
      line: 14,
      evidence: 'const API_KEY = "example"',
      judge_explanation: null,
      fix_prompt: '환경 변수로 이동하세요.',
      easy_description: '비밀정보가 코드에 포함되어 있습니다.',
    },
    {
      id: 2,
      rule_id: 'PII-01',
      title: '개인정보 노출 가능성',
      standard_ref: 'TTAK.KO-12.0259',
      severity: 'medium',
      status: 'review_needed',
      grade_blocking: false,
      file_path: 'src/profile.ts',
      line: 8,
      evidence: null,
      judge_explanation: '사용 맥락 확인 필요',
      fix_prompt: null,
      easy_description: null,
    },
  ],
  review_needed_count: 1,
  sbom_summary: { component_count: 24, vulnerable_count: 4 },
  supply_chain: {
    class: 'B',
    matrix: {
      위험요인: [],
      component_count: 24,
      standard_ref: 'TTAK.KO-12.0414',
      risk_factors: [],
    },
  },
  copy_all_fix_prompts: '환경 변수로 이동하세요.',
}

const easyReport: EasyReport = {
  grade: '위험',
  disclaimer: report.disclaimer,
  easy_descriptions: ['비밀정보가 코드에 포함되어 있습니다.'],
  review_needed_count: 1,
}

const scan: ScanStatus = {
  status: 'done',
  source_type: 'git',
  current_stage: '완료',
  grade: '위험',
  error_message: null,
  previous_comparison: null,
}

const sbom: SbomResponse = {
  components: [
    {
      validation_tool: 'syft',
      supplier: 'OpenJS Foundation',
      author: null,
      component_name: 'lodash',
      version: '4.17.21',
      unique_id: 'pkg:npm/lodash@4.17.21',
      component_hash: null,
      license_name: 'MIT',
      license_usage: 'direct',
      vulnerability_db: null,
      relationship: 'direct',
      release_date: null,
      cve_ids: ['CVE-2021-23337'],
      cvss_base: 7.2,
      cvss_severity: 'high',
      cvss_impact: null,
      cvss_exploitability: null,
      cvss_null_reason: null,
      ecosystem: 'npm',
    },
  ],
  supply_chain_class: 'B',
  parse_markers: [],
  generated_by: 'ansimcode',
}

function renderReport() {
  return renderWithRouter(
    <Routes><Route path="/report/:id" element={<Report />} /></Routes>,
    ['/report/scan-1'],
  )
}

describe('Report', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.getReport.mockImplementation((_id: string, mode: 'dev' | 'easy') =>
      Promise.resolve(mode === 'dev' ? report : easyReport),
    )
    api.getScan.mockResolvedValue(scan)
    api.getSbom.mockResolvedValue(sbom)
    api.getChecklist.mockResolvedValue({ items: [], disclaimer: '자가점검 참고 자료' })
  })

  it('첫 화면에서 확정·검토·취약 컴포넌트 요약을 실제 리포트 데이터로 보여준다', async () => {
    renderReport()

    expect(await screen.findByRole('heading', { name: '진단 리포트' })).toBeInTheDocument()
    const summary = screen.getByRole('region', { name: '진단 결과 요약' })
    expect(within(summary).getByText('확정 발견')).toBeInTheDocument()
    expect(within(summary).getByText('검토 필요')).toBeInTheDocument()
    expect(within(summary).getByText('취약 컴포넌트')).toBeInTheDocument()
    expect(within(summary).getByText('4')).toBeInTheDocument()
  })

  it('SBOM은 해당 탭을 선택했을 때만 상세 표로 보여준다', async () => {
    const user = userEvent.setup()
    renderReport()

    expect(await screen.findByRole('heading', { name: '진단 리포트' })).toBeInTheDocument()
    expect(screen.queryByRole('table', { name: 'SBOM 구성요소' })).not.toBeInTheDocument()

    await user.click(screen.getByRole('tab', { name: /SBOM/ }))

    const sbomTable = await screen.findByRole('table', { name: 'SBOM 구성요소' })
    expect(sbomTable).toBeInTheDocument()
    expect(within(sbomTable).getByRole('columnheader', { name: '공급자' })).toBeInTheDocument()
    expect(within(sbomTable).getByText('OpenJS Foundation')).toBeInTheDocument()
    expect(screen.queryByText('하드코딩된 비밀정보')).not.toBeInTheDocument()
  })

  it('체크리스트와 공급망도 각 탭의 전용 테이블 프레임에서만 보여준다', async () => {
    const user = userEvent.setup()
    api.getChecklist.mockResolvedValue({
      items: [{
        id: 'CHK-01',
        category: '보안 운영',
        question: '취약점 대응 절차가 있습니까?',
        standard_ref: 'TTAK.KO-12.0414',
      }],
      disclaimer: '자가점검 참고 자료',
    })
    api.getReport.mockImplementation((_id: string, mode: 'dev' | 'easy') =>
      Promise.resolve(mode === 'dev' ? {
        ...report,
        supply_chain: {
          ...report.supply_chain,
          matrix: {
            ...report.supply_chain.matrix,
            risk_factors: [{ name: '직접 의존성 취약점', component_count: 2 }],
          },
        },
      } : easyReport),
    )
    renderReport()

    await screen.findByRole('table', { name: '발견 사항 목록' })
    await user.click(screen.getByRole('tab', { name: '체크리스트' }))
    expect(await screen.findByRole('table', { name: '조직 요구사항 체크리스트' })).toBeInTheDocument()
    expect(screen.queryByRole('table', { name: '발견 사항 목록' })).not.toBeInTheDocument()

    await user.click(screen.getByRole('tab', { name: '공급망' }))
    expect(await screen.findByRole('table', { name: '공급망 위험요인' })).toBeInTheDocument()
    expect(screen.queryByRole('table', { name: '조직 요구사항 체크리스트' })).not.toBeInTheDocument()
  })

  it('SBOM과 체크리스트의 데이터 없음 상태를 빈 표와 구분한다', async () => {
    const user = userEvent.setup()
    api.getSbom.mockResolvedValue({ ...sbom, components: [] })
    renderReport()

    await screen.findByRole('table', { name: '발견 사항 목록' })
    await user.click(screen.getByRole('tab', { name: /SBOM/ }))
    expect(await screen.findByText('SBOM 구성요소가 없습니다.')).toBeInTheDocument()
    expect(screen.queryByRole('table', { name: 'SBOM 구성요소' })).not.toBeInTheDocument()

    await user.click(screen.getByRole('tab', { name: '체크리스트' }))
    expect(await screen.findByText('체크리스트 항목이 없습니다.')).toBeInTheDocument()
    expect(screen.queryByRole('table', { name: '조직 요구사항 체크리스트' })).not.toBeInTheDocument()
  })

  it('발견 사항을 필터 가능한 시맨틱 테이블로 보여준다', async () => {
    const user = userEvent.setup()
    renderReport()

    const table = await screen.findByRole('table', { name: '발견 사항 목록' })
    expect(table.querySelector('#finding-1')).toBeInTheDocument()
    expect(within(table).getByText(/하드코딩된 비밀정보/)).toBeInTheDocument()
    expect(within(table).getByText(/개인정보 노출 가능성/)).toBeInTheDocument()

    await user.selectOptions(screen.getByRole('combobox', { name: '심각도 필터' }), 'medium')
    expect(within(table).queryByText(/하드코딩된 비밀정보/)).not.toBeInTheDocument()
    expect(within(table).getByText(/개인정보 노출 가능성/)).toBeInTheDocument()

    await user.selectOptions(screen.getByRole('combobox', { name: '상태 필터' }), 'confirmed')
    expect(screen.getByText('선택한 조건에 맞는 발견 사항이 없습니다.')).toBeInTheDocument()
  })

  it('한 번에 하나의 발견 사항 상세만 인라인으로 펼친다', async () => {
    const user = userEvent.setup()
    renderReport()

    const firstTrigger = await screen.findByRole('button', { name: '하드코딩된 비밀정보 상세 보기' })
    const secondTrigger = screen.getByRole('button', { name: '개인정보 노출 가능성 상세 보기' })

    expect(firstTrigger).toHaveAttribute('aria-expanded', 'false')
    await user.click(firstTrigger)
    expect(firstTrigger).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('const API_KEY = "example"')).toBeVisible()
    expect(screen.getByText('환경 변수로 이동하세요.')).toBeVisible()

    await user.click(secondTrigger)
    expect(secondTrigger).toHaveAttribute('aria-expanded', 'true')
    expect(firstTrigger).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByText('const API_KEY = "example"')).not.toBeInTheDocument()
    expect(screen.getByText('AI 판정 참고: 사용 맥락 확인 필요')).toBeVisible()
  })

  it('시민용 모드에서는 펼친 행에 쉬운 설명을 보여준다', async () => {
    const user = userEvent.setup()
    renderReport()

    await screen.findByRole('heading', { name: '진단 리포트' })
    await user.click(screen.getByRole('checkbox', { name: '시민용 쉬운 설명' }))
    await user.click(screen.getByRole('button', { name: '하드코딩된 비밀정보 상세 보기' }))

    const detail = screen.getByRole('region', { name: '하드코딩된 비밀정보 상세' })
    expect(within(detail).getByText('비밀정보가 코드에 포함되어 있습니다.')).toBeVisible()
    expect(screen.queryByText('const API_KEY = "example"')).not.toBeInTheDocument()
  })

  it('발견 데이터가 없을 때 필터 결과 없음과 구분된 빈 상태를 보여준다', async () => {
    api.getReport.mockImplementation((_id: string, mode: 'dev' | 'easy') =>
      Promise.resolve(mode === 'dev' ? { ...report, findings: [] } : easyReport),
    )
    renderReport()

    expect(await screen.findByText('발견된 사항이 없습니다.')).toBeInTheDocument()
    expect(screen.queryByRole('combobox', { name: '심각도 필터' })).not.toBeInTheDocument()
    expect(screen.queryByText('선택한 조건에 맞는 발견 사항이 없습니다.')).not.toBeInTheDocument()
  })
})
