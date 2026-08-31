import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import ActionButton from './ActionButton'

describe('ActionButton', () => {
  it('disables the button and exposes busy state while loading', () => {
    render(<ActionButton loading>진단 시작</ActionButton>)

    const button = screen.getByRole('button', { name: '진단 시작' })
    expect(button).toBeDisabled()
    expect(button).toHaveAttribute('aria-busy', 'true')
  })
})
