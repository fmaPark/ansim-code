"""SCA 룰 12종 평가 + 0322 §5.1.2 표 5-1 매트릭스.

각 룰의 사양은 `rules/catalog.yaml`(= 계획 Task 2 표)이며 전부 `status="confirmed"`다
— 결정적 사실 판정만 하고 LLM을 경유하지 않는다(G3 등급 결정론).
SCA-03(국내 보안공지 발령)만 예외적으로 파이프라인의 KISA 교차 단계가 만든다.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from packaging.version import InvalidVersion
from packaging.version import parse as parse_version

from app.engine.deps_npm import find_npm_lockfiles
from app.engine.deps_python import find_python_lockfiles
from app.engine.deps_types import Dependency
from app.engine.repo_checks import canon, undeclared_dependencies
from app.engine.sbom import USAGE_NO_NOTICE

log = logging.getLogger(__name__)

STALE_YEARS = 3                                     # SCA-05 장기 미갱신 기준
COPYLEFT_SERVICE_LICENSES = ("AGPL-3.0", "SSPL-1.0")
_SEVERITY_FALLBACK = "medium"

# 0322 §5.1.2 표 5-1 — 공급망 환경 분류별 위험요인.
RISK_FACTORS_0322: dict[str, tuple[str, ...]] = {
    "오픈소스": ("라이선스 위반", "취약점 전파", "업데이트 중단"),
    "바이너리": ("출처 불명", "검증 불가"),
    "자체개발": ("자체 결함 관리",),
}


@dataclass
class FindingDraft:
    rule_id: str
    severity: str
    file_path: str | None
    line: int | None
    evidence: str
    status: str = "confirmed"


def _label(row: dict) -> str:
    return f"{row.get('component_name')} {row.get('version') or '(버전 미상)'}".strip()


def _older_than(release_date: str | None, years: int) -> bool:
    if not release_date:
        return False
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y/%m/%d"):
        try:
            parsed = datetime.strptime(str(release_date)[:len(fmt) + 2].rstrip("Z"), fmt).date()
        except ValueError:
            continue
        return (date.today() - parsed).days > years * 365
    return False


def _is_service_copyleft(license_name: str | None) -> bool:
    """AGPL/SSPL 계열 — 0322 표 5-1 '서비스' 형태 배포 시 공개 의무가 전파된다."""
    u = (license_name or "").upper()
    return u.startswith("AGPL") or "AGPL-3" in u or u.startswith("SSPL") or "SSPL-1" in u


def _is_older(current: str | None, fixed: str | None, ecosystem: str) -> bool:
    """현재 버전 < 수정 버전 (SCA-04). 비교 불가한 문자열이면 판정하지 않는다."""
    if not current or not fixed:
        return False
    try:
        return parse_version(str(current)) < parse_version(str(fixed))
    except InvalidVersion:
        log.debug("버전 비교 불가", extra={"ecosystem": ecosystem, "current": current, "fixed": fixed})
        return False


def evaluate_sca_rules(deps: list[Dependency], sbom_rows: list[dict],
                       imports_py: set[str], imports_js: set[str],
                       root: Path) -> list[FindingDraft]:
    root = Path(root)
    drafts: list[FindingDraft] = []
    has_py_lock = bool(find_python_lockfiles(root))
    has_npm_lock = bool(find_npm_lockfiles(root))
    dep_by_name = {(d.ecosystem, canon(d.name)): d for d in deps}

    # SCA-01 미선언 의존성 — 코드 import − 매니페스트 선언
    for module, ecosystem in undeclared_dependencies(deps, imports_py, imports_js):
        drafts.append(FindingDraft(
            rule_id="SCA-01", severity="medium", file_path=None, line=None,
            evidence=f"미선언 의존성: 코드가 `{module}`을(를) import 하지만 "
                     f"{'requirements/pyproject' if ecosystem == 'pypi' else 'package.json'}에 선언이 없습니다"))

    for row in sbom_rows:
        label = _label(row)
        cve_ids = row.get("cve_ids") or []
        vuln_entries = row.get("vulnerability_db") or []

        # SCA-02 알려진 취약 버전(CVE) — severity는 cvss_severity를 따른다
        if cve_ids:
            cvss = row.get("cvss_base")
            drafts.append(FindingDraft(
                rule_id="SCA-02", severity=row.get("cvss_severity") or _SEVERITY_FALLBACK,
                file_path=None, line=None,
                evidence=f"{label} — 알려진 취약점 {', '.join(cve_ids)}"
                         + (f" (CVSS Base {cvss})" if cvss is not None else " (CVSS 벡터 미제공)")))

        # SCA-04 패치 미적용 — OSV가 알려준 fixed 버전이 있고 현재 버전이 그보다 낮다
        fixed_versions = sorted({e.get("fixed") for e in vuln_entries if e.get("fixed")})
        outdated = [f for f in fixed_versions if _is_older(row.get("version"), f, row.get("ecosystem", ""))]
        if outdated:
            drafts.append(FindingDraft(
                rule_id="SCA-04", severity="medium", file_path=None, line=None,
                evidence=f"{label} — 수정 버전 {', '.join(outdated)}이(가) 공개되었으나 적용되지 않았습니다"))

        # SCA-05 장기 미갱신 컴포넌트 (정보성 — Low는 등급에 기여하지 않는다)
        if _older_than(row.get("release_date"), STALE_YEARS):
            drafts.append(FindingDraft(
                rule_id="SCA-05", severity="low", file_path=None, line=None,
                evidence=f"{label} — 최종 배포일 {row.get('release_date')}로 {STALE_YEARS}년 이상 갱신되지 않았습니다"))

        # SCA-06 라이선스 복제·고지 없음 (0309 §6.8·§6.9 3축 판정)
        if row.get("license_usage") == USAGE_NO_NOTICE:
            drafts.append(FindingDraft(
                rule_id="SCA-06", severity="medium", file_path=None, line=None,
                evidence=f"{label} — 저장소에 복제되어 있으나 LICENSE·COPYING 고지 파일이 없습니다"))

        # SCA-07 AGPL/SSPL 서비스 배포 경고 (0322 §5.1.2 표 5-1 '서비스')
        license_name = row.get("license_name") or ""
        if _is_service_copyleft(license_name):
            drafts.append(FindingDraft(
                rule_id="SCA-07", severity="medium", file_path=None, line=None,
                evidence=f"{label} — {license_name} 컴포넌트입니다. 0322 표 5-1의 '서비스' 형태로 "
                         f"배포하면 소스 공개 의무가 서비스 전체에 전파될 위험이 있습니다"))

        # SCA-08 라이선스 불명 (0309 §6.8)
        if not license_name:
            drafts.append(FindingDraft(
                rule_id="SCA-08", severity="low", file_path=None, line=None,
                evidence=f"{label} — 매니페스트·동봉 파일에서 라이선스를 확인할 수 없습니다"))

        # SCA-09 컴포넌트 해시 부재 (0309 §6.7)
        if not row.get("component_hash"):
            drafts.append(FindingDraft(
                rule_id="SCA-09", severity="low", file_path=None, line=None,
                evidence=f"{label} — lock 파일이 없거나 integrity/hash 필드가 없어 무결성을 검증할 수 없습니다"))

    for dep in deps:
        has_lock = has_py_lock if dep.ecosystem == "pypi" else has_npm_lock

        # SCA-10 출처 불명 컴포넌트 (0309 §6.2·§6.6)
        if not dep.registry_source:
            drafts.append(FindingDraft(
                rule_id="SCA-10", severity="medium", file_path=dep.declared_in, line=None,
                evidence=f"{dep.name} — 공개 레지스트리가 아닌 출처(git·로컬 경로·URL 등)에서 가져옵니다"))

        # vendored 복제본은 선언·lock의 대상이 아니다 — SCA-06·10이 담당한다.
        if dep.vendored_path:
            continue

        # SCA-11 버전 미고정 (0259 §9.3)
        if not dep.is_pinned and not has_lock:
            drafts.append(FindingDraft(
                rule_id="SCA-11", severity="low", file_path=dep.declared_in, line=None,
                evidence=f"{dep.name} — 버전이 고정되지 않았고 lock 파일도 없어 설치 시점마다 버전이 달라질 수 있습니다"))

        # SCA-12 매니페스트-lock 불일치 (0259 §9.3 갭 분석)
        # lock에만 있고 선언에 없는 항목은 정상적인 transitive이므로 세지 않는다.
        if has_lock and dep.relationship == "direct" and not dep.in_lock:
            drafts.append(FindingDraft(
                rule_id="SCA-12", severity="medium", file_path=dep.declared_in, line=None,
                evidence=f"{dep.name} — {dep.declared_in}에 선언되어 있으나 lock 파일에 해당 항목이 없습니다"))

    log.info("SCA 룰 평가", extra={"draft_count": len(drafts), "dep_count": len(dep_by_name)})
    return drafts


def matrix_0322(supply_chain_class: str | None, sbom_rows: list[dict]) -> dict:
    """0322 §5.1.2 표 5-1 룩업 — 분류별 위험요인 + 해당 컴포넌트 수."""
    counters = {
        "라이선스 위반": sum(1 for r in sbom_rows
                        if r.get("license_usage") == USAGE_NO_NOTICE
                        or _is_service_copyleft(r.get("license_name"))),
        "취약점 전파": sum(1 for r in sbom_rows if r.get("cve_ids")),
        "업데이트 중단": sum(1 for r in sbom_rows if _older_than(r.get("release_date"), STALE_YEARS)),
        "출처 불명": sum(1 for r in sbom_rows if not r.get("supplier")),
        "검증 불가": sum(1 for r in sbom_rows if not r.get("component_hash")),
        "자체 결함 관리": len(sbom_rows),
    }
    factors = RISK_FACTORS_0322.get(supply_chain_class or "", ())
    return {
        "standard_ref": "TTAK.KO-11.0322 §5.1.2 표 5-1",
        "supply_chain_class": supply_chain_class,
        "component_count": len(sbom_rows),
        "risk_factors": [{"name": name, "component_count": counters.get(name, 0)} for name in factors],
    }
