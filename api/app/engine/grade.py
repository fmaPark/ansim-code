"""등급 결정론 (P0-3, Task 17) — TDD §4.5 등급 산정 규칙의 구현.

`calc_grade`는 **static confirmed 발견과 CVE만의 순수 함수**다(G3). LLM 산출물
(judge_explanation 등)은 인자 자체에 존재하지 않으므로 등급에 기여할 구조적
경로가 없다 — 같은 (콘텐츠 지문, rule_catalog_version, vuln_db_snapshot_date)이면
등급이 항상 같다.
"""
from dataclasses import dataclass, field

DANGER, CAUTION, SAFE = "위험", "주의", "안심"

# 등급에 기여하는 CVE 심각도 — low는 정보 표기만(TDD §4.5).
CRITICAL_CVE = {"critical"}
CAUTION_CVE = {"high", "medium"}


@dataclass(frozen=True)
class GradeResult:
    grade: str
    blocking_finding_ids: list = field(default_factory=list)
    blocking_cve_ids: list = field(default_factory=list)
    upgrade_target: str | None = None
    upgrade_count: int = 0


def _get(row, key):
    """dict·ORM 행·dataclass를 모두 받는다 — 호출부가 어댑터를 만들지 않게."""
    return row.get(key) if isinstance(row, dict) else getattr(row, key, None)


def _is_danger_finding(f) -> bool:
    """즉시 유출로 이어지는 결함 — 시크릿 confirmed, 개인정보 평문 저장(P6) confirmed."""
    rule_id = _get(f, "rule_id") or ""
    return _get(f, "status") == "confirmed" and (rule_id.startswith("SEC-") or rule_id == "P6")


def _grade_of(findings, cve_rows) -> str:
    confirmed = [f for f in findings if _get(f, "status") == "confirmed"]
    severities = {(_get(c, "cvss_severity") or "").lower() for c in cve_rows}

    if any(_is_danger_finding(f) for f in confirmed) or severities & CRITICAL_CVE:
        return DANGER
    if confirmed or severities & CAUTION_CVE:
        return CAUTION
    return SAFE


def _blocking(findings, cve_rows, grade: str):
    """현재 등급을 만든 발견들 — 이것을 없애면 등급이 오른다."""
    if grade == DANGER:
        f_block = [f for f in findings if _is_danger_finding(f)]
        c_block = [c for c in cve_rows
                   if (_get(c, "cvss_severity") or "").lower() in CRITICAL_CVE]
    elif grade == CAUTION:
        f_block = [f for f in findings if _get(f, "status") == "confirmed"]
        c_block = [c for c in cve_rows
                   if (_get(c, "cvss_severity") or "").lower() in CAUTION_CVE]
    else:
        f_block, c_block = [], []
    return f_block, c_block


def calc_grade(findings, cve_rows) -> GradeResult:
    """안전등급 산정 + 상향 조건.

    findings: (id, rule_id, status, severity)를 가진 행. cve_rows: (cve_id, cvss_severity).
    상향 조건은 blocking을 제거한 입력으로 **재귀 1회 재계산**해 도달 등급·건수를 구한다.
    """
    grade = _grade_of(findings, cve_rows)
    f_block, c_block = _blocking(findings, cve_rows, grade)

    upgrade_target, upgrade_count = None, 0
    if grade != SAFE:
        blocked_f = {id(f) for f in f_block}
        blocked_c = {id(c) for c in c_block}
        upgrade_target = _grade_of([f for f in findings if id(f) not in blocked_f],
                                   [c for c in cve_rows if id(c) not in blocked_c])
        upgrade_count = len(f_block) + len(c_block)

    return GradeResult(
        grade=grade,
        blocking_finding_ids=[_get(f, "id") for f in f_block],
        blocking_cve_ids=[_get(c, "cve_id") for c in c_block],
        upgrade_target=upgrade_target,
        upgrade_count=upgrade_count,
    )


def cve_rows_from_osv(osv_result) -> list[dict]:
    """OsvResult → calc_grade 입력. CVE별 **최고 심각도 1건**으로 정규화한다.

    컴포넌트의 대표 CVSS(_apply_vulns의 최고 Base)를 그 컴포넌트의 모든 CVE에
    적용하면 critical이 과대 전파되므로, CVE가 실제로 속한 취약점의 등급만 쓴다.
    """
    order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "unknown": 0}
    worst: dict[str, str] = {}
    for infos in osv_result.vulns.values():
        for vuln in infos:
            severity = (vuln.severity or "unknown").lower()
            for cve in vuln.cve_ids:
                if order.get(severity, 0) > order.get(worst.get(cve, "unknown"), 0):
                    worst[cve] = severity
    return [{"cve_id": cve, "cvss_severity": sev} for cve, sev in sorted(worst.items())]
