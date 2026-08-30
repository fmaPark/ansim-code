"""PyPI/npm 레지스트리 메타데이터 조회 — SBOM ⑧ license_name·⑫ release_date 보강(이슈 #33).

장애 정책은 OSV 클라이언트와 동일: 어떤 호출이 실패해도 예외로 스캔을 죽이지 않는다.
얻은 만큼만 돌려주고 `incomplete=True`를 세워 리포트가 "일부 미조회"를 표시하게 한다.
404는 결정적 부정 응답(사내 패키지명·야인 버전)이라 incomplete로 치지 않는다.

버전 미고정 의존성은 최신 릴리스를 조회한다 — "지금 설치하면 받게 될 것"의
라이선스·배포일이므로 SCA-05(장기 미갱신)·SCA-07(서비스 카피레프트) 의미론에 맞다.
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import date
from urllib.parse import quote

import httpx

from app.engine.sbom import normalize_license

log = logging.getLogger(__name__)

PYPI_API_BASE = "https://pypi.org"
NPM_API_BASE = "https://registry.npmjs.org"
REGISTRY_TIMEOUT_SECONDS = 10.0   # OSV와 동일 (TDD §4.6)
REGISTRY_RETRIES = 1              # 실패 시 재시도 1회
REGISTRY_CONCURRENCY = 8          # 패키지별 조회 병렬 상한

_USER_AGENT = "AnsimCode-SCA/1.0"   # 레이트리밋 식별용 UA (PyPI 권고)
_NOT_FOUND = object()               # 404 센티널 — 장애가 아니라 확정 부정 응답


@dataclass(frozen=True)
class RegistryQuery:
    key: str              # purl(unique_id) — 결과 매핑 키
    ecosystem: str        # "pypi" | "npm"
    name: str
    version: str | None   # None = 미고정 → 최신 릴리스 의미론


@dataclass
class ComponentMetadata:
    license_name: str | None    # SPDX 정규화·128자 이내
    release_date: str | None    # YYYY-MM-DD


@dataclass
class RegistryResult:
    metadata: dict[str, ComponentMetadata]   # key = purl
    incomplete: bool


def registry_snapshot_label() -> str:
    """G11 재현성 기록 — 조회 시점을 `registry@YYYY-MM-DD`로 남긴다."""
    return f"registry@{date.today().isoformat()}"


async def _request(client: httpx.AsyncClient, url: str):
    """GET 1회 — 404는 재시도 없이 _NOT_FOUND, 그 외 실패는 재시도 후 None."""
    for attempt in range(REGISTRY_RETRIES + 1):
        try:
            r = await client.get(url)
            if r.status_code == 404:
                return _NOT_FOUND
            r.raise_for_status()
            return r.json()
        except Exception as e:                       # 타임아웃·연결 실패·5xx·JSON 오류 모두
            if attempt >= REGISTRY_RETRIES:
                log.warning("레지스트리 호출 실패",
                            extra={"registry_url": url, "error": f"{type(e).__name__}: {e}"})
                return None
    return None


def _date_only(raw) -> str | None:
    """ISO 타임스탬프(소수점 초 포함) → YYYY-MM-DD — sca_rules._older_than이 파싱 가능한 형식."""
    s = str(raw or "")[:10]
    return s if len(s) == 10 else None


def _pypi_metadata(data: dict) -> ComponentMetadata:
    info = data.get("info") or {}
    license_name = None
    # license_expression(신 메타데이터) → license → classifiers 순 — 앞 후보가
    # 정규화 불능(전문 blob 등)이면 다음 후보로 폴스루한다.
    candidates = [info.get("license_expression"), info.get("license")]
    candidates += [str(c).split("::")[-1].strip()
                   for c in info.get("classifiers") or [] if str(c).startswith("License ::")]
    for cand in candidates:
        license_name = normalize_license(cand if cand is None else str(cand))
        if license_name:
            break

    uploads = [u.get("upload_time_iso_8601") or u.get("upload_time")
               for u in data.get("urls") or []]
    uploads = sorted(u for u in uploads if u)
    return ComponentMetadata(license_name=license_name,
                             release_date=_date_only(uploads[0]) if uploads else None)


def _npm_metadata(data: dict, version: str | None) -> ComponentMetadata:
    versions = data.get("versions") or {}
    v = version if version in versions else (data.get("dist-tags") or {}).get("latest")
    entry = versions.get(v) or {}
    lic = entry.get("license")
    if isinstance(lic, dict):        # 레거시 {"type": "MIT", ...} 형식
        lic = lic.get("type")
    release = (data.get("time") or {}).get(v) if v else None
    return ComponentMetadata(license_name=normalize_license(lic if lic is None else str(lic)),
                             release_date=_date_only(release))


async def _fetch(client: httpx.AsyncClient, ecosystem: str, name: str,
                 version: str | None) -> ComponentMetadata | None:
    """패키지 1건 조회. None = 장애(incomplete), 메타데이터 없음은 빈 ComponentMetadata."""
    if ecosystem == "pypi":
        name = re.sub(r"[-_.]+", "-", name).lower()          # PEP 503 정규화 — 리다이렉트 회피
        path = f"/pypi/{name}/{version}/json" if version else f"/pypi/{name}/json"
        data = await _request(client, f"{PYPI_API_BASE}{path}")
        if data is None:
            return None
        if data is _NOT_FOUND:
            return ComponentMetadata(None, None)
        return _pypi_metadata(data)
    if ecosystem == "npm":
        # 축약 문서(Accept: vnd.npm.install-v1)는 time을 누락한다 — 전체 문서만 쓴다.
        data = await _request(client, f"{NPM_API_BASE}/{quote(name, safe='@')}")
        if data is None:
            return None
        if data is _NOT_FOUND:
            return ComponentMetadata(None, None)
        return _npm_metadata(data, version)
    return ComponentMetadata(None, None)


async def query_registry(queries: list[RegistryQuery],
                         transport: httpx.BaseTransport | None = None) -> RegistryResult:
    """질의 목록 → {purl: ComponentMetadata}. 같은 패키지는 1회만 조회한다."""
    queries = [q for q in queries if q.key and q.name and q.ecosystem in ("pypi", "npm")]
    if not queries:
        return RegistryResult(metadata={}, incomplete=False)

    unique: dict[tuple, list[RegistryQuery]] = {}
    for q in queries:
        unique.setdefault((q.ecosystem, q.name.lower(), q.version), []).append(q)

    incomplete = False
    metadata: dict[str, ComponentMetadata] = {}
    semaphore = asyncio.Semaphore(REGISTRY_CONCURRENCY)

    async with httpx.AsyncClient(timeout=REGISTRY_TIMEOUT_SECONDS, transport=transport,
                                 headers={"User-Agent": _USER_AGENT}) as client:

        async def fetch(key: tuple, group: list[RegistryQuery]):
            async with semaphore:
                q = group[0]
                return group, await _fetch(client, q.ecosystem, q.name, q.version)

        for group, meta in await asyncio.gather(*(fetch(k, g) for k, g in unique.items())):
            if meta is None:
                incomplete = True                     # 부분 결과 유지 — 나머지는 계속 쓴다
                continue
            if meta.license_name or meta.release_date:
                for q in group:
                    metadata[q.key] = meta

    return RegistryResult(metadata=metadata, incomplete=incomplete)
