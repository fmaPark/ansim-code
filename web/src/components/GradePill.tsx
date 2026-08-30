import type { Grade } from '../api/client'

const KNOWN: readonly string[] = ['안심', '주의', '위험']

export default function GradePill({ grade, big }: { grade: Grade | string | null; big?: boolean }) {
  const cls = grade && KNOWN.includes(grade) ? `grade-${grade}` : 'grade-none'
  return <span className={`grade-pill ${cls}${big ? ' big' : ''}`}>{grade ?? '등급 없음'}</span>
}
