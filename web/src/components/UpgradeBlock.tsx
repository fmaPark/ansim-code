import type { UpgradeBlock as UpgradeData } from '../api/client'

export default function UpgradeBlock({ data }: { data: UpgradeData }) {
  return (
    <div className="upgrade-block">
      <strong>{data.message}</strong>
      <div className="upgrade-targets">
        {data.blocking_finding_ids.map((id) => (
          <a key={id} href={`#finding-${id}`} className="upgrade-anchor">
            발견 #{id}
          </a>
        ))}
        {data.blocking_cve_ids.map((cve) => (
          <span key={cve} className="upgrade-anchor cve">
            {cve}
          </span>
        ))}
      </div>
    </div>
  )
}
