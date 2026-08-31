import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import PublishFlow from './PublishFlow'

const publish = vi.hoisted(() => vi.fn(() => new Promise(() => {})))

vi.mock('../api/client', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api/client')>()),
  publish,
}))

it('opens an accessible dialog and restores focus after Escape', async () => {
  const user = userEvent.setup()
  render(<PublishFlow scanId="scan-1" sourceType="git" />)

  const trigger = screen.getByRole('button', { name: '공개하기' })
  await user.click(trigger)
  expect(screen.getByRole('dialog', { name: '등급 공개 — 저장소 소유 증명' })).toBeVisible()

  await user.keyboard('{Escape}')
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(trigger).toHaveFocus()
})
