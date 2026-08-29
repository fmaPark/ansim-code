"""OSV.dev 대조 클라이언트 (TDD §4.6 — purl 배치 질의·무인증).

장애 정책(TDD §6): 어떤 호출이 실패해도 예외로 스캔을 죽이지 않는다. 얻은 만큼만
돌려주고 `incomplete=True`를 세워 리포트가 "일부 미대조"를 표시하게 한다.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import date

import httpx

from app.engine.cvss import derive_cvss3

log = logging.getLogger(__name__)

OSV_API_BASE = "https://api.osv.dev"
OSV_TIMEOUT_SECONDS = 10.0        # 모든 호출 공통 (TDD §4.6)
OSV_RETRIES = 1                   # 실패 시 재시도 1회
OSV_BATCH_SIZE = 1000             # querybatch 1회 질의 상한
OSV_DETAIL_CONCURRENCY = 8        # /v1/vulns/{id} 병렬 상한


@dataclass
class VulnInfo:
    id: str
    cve_ids: list[str] = field(default_factory=list)
    cvss_vector: str | None = None
    severity: str = "unknown"
    fixed_version: str | None = None
    source: str = "OSV"


@dataclass
class OsvResult:
    vulns: dict[str, list[VulnInfo]]
    incomplete: bool


def osv_snapshot_date() -> str:
    """G11 재현성 기록 — 대조 시점을 `OSV@YYYY-MM-DD`로 남긴다."""
    return f"OSV@{date.today().isoformat()}"


async def _request(client: httpx.AsyncClient, method: str, url: str, **kw) -> dict | None:
    for attempt in range(OSV_RETRIES + 1):
        try:
            r = await client.request(method, url, **kw)
            r.raise_for_status()
            return r.json()
        except Exception as e:                       # 타임아웃·연결 실패·5xx·JSON 오류 모두
            if attempt >= OSV_RETRIES:
                log.warning("OSV 호출 실패", extra={"osv_url": url, "error": f"{type(e).__name__}: {e}"})
                return None
    return None


def _to_vuln_info(vuln_id: str, detail: dict) -> VulnInfo:
    aliases = [a for a in (detail.get("aliases") or []) if str(a).startswith("CVE-")]
    if vuln_id.startswith("CVE-") and vuln_id not in aliases:
        aliases.insert(0, vuln_id)

    vector = None
    for entry in detail.get("severity") or []:
        if entry.get("type") == "CVSS_V3" and entry.get("score"):
            vector = entry["score"]
            break

    fixed = None
    for affected in detail.get("affected") or []:
        for rng in affected.get("ranges") or []:
            for event in rng.get("events") or []:
                if event.get("fixed"):
                    fixed = event["fixed"]
                    break
            if fixed:
                break
        if fixed:
            break

    derived = derive_cvss3(vector)
    if derived:
        severity = derived[3]
    else:
        raw = ((detail.get("database_specific") or {}).get("severity") or "").lower()
        severity = raw if raw in {"critical", "high", "medium", "low"} else "unknown"

    return VulnInfo(id=vuln_id, cve_ids=aliases, cvss_vector=vector,
                    severity=severity, fixed_version=fixed, source="OSV")


async def query_osv(purls: list[str], transport: httpx.BaseTransport | None = None) -> OsvResult:
    """purl 목록 → {purl: [VulnInfo]}. 스캔 1회 안에서 vuln 상세는 dict로 캐시한다."""
    purls = [p for p in purls if p]
    if not purls:
        return OsvResult(vulns={}, incomplete=False)

    incomplete = False
    ids_by_purl: dict[str, list[str]] = {}

    async with httpx.AsyncClient(base_url=OSV_API_BASE, timeout=OSV_TIMEOUT_SECONDS,
                                 transport=transport) as client:
        for start in range(0, len(purls), OSV_BATCH_SIZE):
            chunk = purls[start:start + OSV_BATCH_SIZE]
            body = {"queries": [{"package": {"purl": p}} for p in chunk]}
            data = await _request(client, "POST", "/v1/querybatch", json=body)
            if data is None:
                incomplete = True
                continue
            for purl, entry in zip(chunk, data.get("results") or []):
                ids = [v["id"] for v in (entry or {}).get("vulns") or [] if v.get("id")]
                if ids:
                    ids_by_purl.setdefault(purl, []).extend(ids)

        cache: dict[str, VulnInfo] = {}
        unique_ids = sorted({i for ids in ids_by_purl.values() for i in ids})
        semaphore = asyncio.Semaphore(OSV_DETAIL_CONCURRENCY)

        async def fetch(vuln_id: str):
            async with semaphore:
                return vuln_id, await _request(client, "GET", f"/v1/vulns/{vuln_id}")

        for vuln_id, detail in await asyncio.gather(*(fetch(i) for i in unique_ids)):
            if detail is None:
                incomplete = True
                cache[vuln_id] = VulnInfo(id=vuln_id)     # 부분 결과 유지 — ID는 남긴다
            else:
                cache[vuln_id] = _to_vuln_info(vuln_id, detail)

    return OsvResult(vulns={p: [cache[i] for i in ids] for p, ids in ids_by_purl.items()},
                     incomplete=incomplete)
