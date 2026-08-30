import { screen } from '@testing-library/react'
import { Route, Routes } from 'react-router-dom'
import { expect, it, vi } from 'vitest'
import { renderWithRouter } from '../test/render'
import ScanProgress from './ScanProgress'

const api = vi.hoisted(() => ({
  pollScan: vi.fn(() => new Promise(() => {})),
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
