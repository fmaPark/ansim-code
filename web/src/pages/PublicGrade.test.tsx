import { screen } from '@testing-library/react'
import { Route, Routes } from 'react-router-dom'
import { expect, it, vi } from 'vitest'
import { renderWithRouter } from '../test/render'
import PublicGrade from './PublicGrade'

const api = vi.hoisted(() => ({
  getPublicGrade: vi.fn(),
}))

vi.mock('../api/client', () => api)

it('공개 등급과 게시 주체 안내를 명확하게 보여준다', async () => {
  api.getPublicGrade.mockResolvedValue({
    grade: '안심',
    scanned_at: '2026-08-31T00:00:00Z',
    easy_report: { easy_descriptions: [], review_needed_count: 0 },
    provenance: {},
    disclaimer: '본 결과는 인증이 아닌 자가점검 참고 자료입니다.',
  })

  renderWithRouter(
    <Routes><Route path="/g/:slug" element={<PublicGrade />} /></Routes>,
    ['/g/demo'],
  )

  expect(await screen.findByRole('heading', { name: '공개 안전등급' })).toBeInTheDocument()
  expect(screen.getByText('이 등급은 공개 git 저장소 소유자가 직접 공개했습니다.')).toBeInTheDocument()
})
