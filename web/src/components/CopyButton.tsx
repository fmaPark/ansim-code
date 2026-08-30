import { useRef, useState } from 'react'

export default function CopyButton({ text, label = '복사' }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout>>(null)

  function markCopied() {
    setCopied(true)
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(() => setCopied(false), 1800)
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(text)
      markCopied()
    } catch {
      // 클립보드 API가 막힌 환경(비보안 컨텍스트 등) — 레거시 execCommand로 폴백
      const ta = document.createElement('textarea')
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      const ok = document.execCommand('copy')
      ta.remove()
      if (ok) markCopied()
      else window.prompt('클립보드 접근이 차단되었습니다. 직접 복사하세요:', text)
    }
  }

  return (
    <button type="button" className={`ghost copy-btn${copied ? ' copied' : ''}`} onClick={copy}>
      {copied ? '복사됨 ✓' : label}
    </button>
  )
}
