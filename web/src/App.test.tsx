import { render, screen } from '@testing-library/react'
import { expect, it } from 'vitest'
import App from './App'

it('홈 화면에서 자가점검 안내를 한 번만 보여준다', () => {
  render(<App />)

  expect(screen.getAllByText(/인증이 아닌 자가점검 보조 도구입니다\./)).toHaveLength(1)
})
