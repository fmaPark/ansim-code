import { render, screen } from '@testing-library/react'
import { expect, it } from 'vitest'
import SixPrinciples from './SixPrinciples'

it('진단 가능 여부와 발견 건수로 6대 원칙 상태를 구분한다', () => {
  render(
    <SixPrinciples
      axes={[
        { principle: '목적 제한', rules: ['PII-01'], finding_count: 0 },
        { principle: '안전성', rules: ['SEC-01'], finding_count: 2 },
        { principle: '보유 기간 제한', rules: [], finding_count: 0, note: '체크리스트 확인' },
      ]}
    />,
  )

  expect(screen.getByText('준수')).toBeInTheDocument()
  expect(screen.getByText('위반')).toBeInTheDocument()
  expect(screen.getByText('확인 필요')).toBeInTheDocument()
})
