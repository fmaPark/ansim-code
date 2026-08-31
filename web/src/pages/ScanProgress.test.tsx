import { screen } from '@testing-library/react'
import { Route, Routes } from 'react-router-dom'
import { expect, it, vi } from 'vitest'
import type { ScanStatus } from '../api/client'
import { renderWithRouter } from '../test/render'
import ScanProgress from './ScanProgress'

const api = vi.hoisted(() => ({
  pollScan: vi.fn(
    (_id: string, _onUpdate: (state: ScanStatus) => void): Promise<ScanStatus | null> =>
      new Promise(() => {}),
  ),
}))

vi.mock('../api/client', () => api)

it('진단 단계와 현재 상태를 보조 기술에 알린다', () => {
  renderWithRouter(
    <Routes><Route path="/scan/:id" element={<ScanProgress />} /></Routes>,
    ['/scan/scan-1'],
  )

  expect(screen.getByRole('heading', { name: '진단 진행 중' })).toBeInTheDocument()
  expect(screen.getByRole('status')).toHaveTextContent('대기 중')
  expect(screen.getByLabelText('진단 진행 단계')).toBeInTheDocument()
})

it('현재 단계에 대응하는 전체 진행률을 원형 진행 표시로 보여준다', async () => {
  const state: ScanStatus = {
    status: 'running',
    source_type: 'git',
    current_stage: '위험분석',
    grade: null,
    error_message: null,
    previous_comparison: null,
  }
  api.pollScan.mockImplementation((_id, onUpdate) => {
    onUpdate(state)
    return new Promise<ScanStatus | null>(() => {})
  })

  renderWithRouter(
    <Routes><Route path="/scan/:id" element={<ScanProgress />} /></Routes>,
    ['/scan/scan-1'],
  )

  const progress = await screen.findByRole('progressbar', { name: '전체 진단 진행률' })
  expect(progress).toHaveAttribute('aria-valuenow', '60')
  expect(screen.getByRole('heading', { name: '위험분석을 진행하고 있습니다' })).toBeInTheDocument()
})
