import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it } from 'vitest'
import FindingCard from './FindingCard'

it('exposes the fix prompt as an accessible disclosure', async () => {
  const user = userEvent.setup()
  render(
    <FindingCard
      easy={false}
      finding={{
        id: 1,
        rule_id: 'SEC-001',
        title: '비밀정보 노출',
        standard_ref: 'TTAK.KO-12.0259',
        severity: 'high',
        status: 'confirmed',
        grade_blocking: true,
        file_path: 'src/config.ts',
        line: 14,
        evidence: null,
        judge_explanation: null,
        fix_prompt: '환경 변수로 이동하세요.',
        easy_description: null,
      }}
    />,
  )

  const trigger = screen.getByRole('button', { name: /수정 프롬프트 보기/ })
  expect(trigger).toHaveAttribute('aria-expanded', 'false')
  await user.click(trigger)
  expect(trigger).toHaveAttribute('aria-expanded', 'true')
  expect(screen.getByText('환경 변수로 이동하세요.')).toBeVisible()
})
