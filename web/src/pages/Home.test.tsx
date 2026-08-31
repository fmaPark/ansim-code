import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { renderWithRouter } from '../test/render'
import Home from './Home'

const { startGitScan, startZipScan } = vi.hoisted(() => ({
  startGitScan: vi.fn(),
  startZipScan: vi.fn(),
}))

vi.mock('../api/client', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api/client')>()
  return {
    ...actual,
    startGitScan,
    startZipScan,
  }
})

describe('Home', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('provides an accessible label for the public git URL', () => {
    renderWithRouter(<Home />)

    expect(screen.getByRole('textbox', { name: '공개 git 저장소' })).toBeVisible()
  })

  it('announces a non-HTTPS URL error without starting a scan', async () => {
    const user = userEvent.setup()
    renderWithRouter(<Home />)

    await user.type(screen.getByRole('textbox'), 'http://example.com/repo')
    await user.click(screen.getByRole('button', { name: '진단 시작' }))

    expect(screen.getByRole('alert')).toHaveTextContent('공개 https git URL만 지원합니다')
    expect(startGitScan).not.toHaveBeenCalled()
  })

  it('opens the zip picker from the keyboard', async () => {
    const user = userEvent.setup()
    const click = vi.spyOn(HTMLInputElement.prototype, 'click').mockImplementation(() => {})
    renderWithRouter(<Home />)

    screen.getByRole('button', { name: 'zip 파일 업로드' }).focus()
    await user.keyboard('{Enter}')

    expect(click).toHaveBeenCalledOnce()
    click.mockRestore()
  })
})
