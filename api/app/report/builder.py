"""이중 리포트 조립 (Task 19) — TDD §3·§4.4·§4.5, 0259 §9.3(감사보고서 형식), 0322 §5.1.2.

산출 JSON의 키는 **프론트(S5)와의 계약**이다(계획 문서 Task 19). 임의 개명 금지.
개발자용은 조항 인용 + 6대 원칙 축 + 상향 조건 + 복사용 프롬프트, 시민용은 등급과
쉬운 설명만 담는다. 원본 코드는 이미 파기된 뒤이므로 입력은 DB 행뿐이다(G1).
"""
import logging

from app.engine.analysis import _catalog
from app.engine.grade import SAFE

log = logging.getLogger(__name__)

DISCLAIMER = "본 결과는 인증이 아닌 자가점검 보조 도구입니다."

# 0414 §7.3.1 6대 원칙 축 — 자동 진단이 닿지 않는 축은 note로 체크리스트를 안내한다(TDD §3).
SIX_PRINCIPLES: list[dict] = [
    {"principle": "적법성", "rules": ["P1", "P2", "P3", "P5"]},
    {"principle": "안전성", "rules": ["P6", "P7", "P8", "SEC-05"]},
    {"principle": "투명성", "rules": ["P9"]},
    {"principle": "참여성", "rules": [], "note": "정보주체 권리 — 체크리스트 안내"},
    {"principle": "책임성", "rules": ["P4", "P10"], "note": "조직 체크리스트 병행"},
    {"principle": "공정성", "rules": [], "note": "자동 진단 범위 밖 — 체크리스트 안내"},
]


def _location(f) -> str:
    if not f.file_path:
        return "저장소 전체"
    return f"{f.file_path}:{f.line}" if f.line else f.file_path


def _finding_row(f) -> dict:
    rule = _catalog().get(f.rule_id, {})
    return {
        "id": f.id,
        "rule_id": f.rule_id,
        "title": rule.get("title", f.rule_id),
        "standard_ref": rule.get("standard_ref", ""),   # 조항 인용 리포트(0259 §9.3)
        "severity": f.severity,
        "status": f.status,
        "grade_blocking": bool(f.grade_blocking),
        "file_path": f.file_path,
        "line": f.line,
        "evidence": f.evidence,                          # 항상 마스킹본 (G2)
        "judge_explanation": f.judge_explanation,
        "fix_prompt": f.fix_prompt,
        "easy_description": f.easy_description,
    }


def _six_principles(findings) -> list[dict]:
    axes = []
    for axis in SIX_PRINCIPLES:
        rules = set(axis["rules"])
        entry = {"principle": axis["principle"], "rules": axis["rules"],
                 "finding_count": sum(1 for f in findings if f.rule_id in rules)}
        if axis.get("note"):
            entry["note"] = axis["note"]
        axes.append(entry)
    return axes


def _particle(word: str) -> str:
    """'로/으로' 선택 — 받침 있는 '안심'은 '안심으로', 없는 '주의'는 '주의로'."""
    if not word:
        return "로"
    last = ord(word[-1])
    if not 0xAC00 <= last <= 0xD7A3:            # 한글 음절이 아니면 기본형
        return "로"
    jong = (last - 0xAC00) % 28
    return "로" if jong in (0, 8) else "으로"   # 받침 없음·ㄹ 받침은 '로'


def _upgrade(grade: str, grade_result) -> dict | None:
    """등급 상향 조건 블록 — 재진단 루프의 payoff (TDD §4.5)."""
    if grade == SAFE or grade_result is None or not grade_result.upgrade_target:
        return None
    target = grade_result.upgrade_target
    count = grade_result.upgrade_count
    return {
        "target": target,
        "count": count,          # 발견 + CVE 합계 — 아래 두 목록의 길이 합과 같다
        "message": f"이 {count}건만 해결하면 {target}{_particle(target)} 올라갑니다",
        "blocking_finding_ids": list(grade_result.blocking_finding_ids),
        "blocking_cve_ids": list(grade_result.blocking_cve_ids),
    }


def _supply_chain(scan, matrix: dict | None) -> dict:
    """0322 표 5-1 매트릭스를 프론트 계약 형태로 어댑트(원본 상세는 risk_factors로 보존)."""
    matrix = matrix or {}
    return {
        "class": scan.supply_chain_class,
        "matrix": {
            "위험요인": [f["name"] for f in matrix.get("risk_factors", [])],
            "component_count": matrix.get("component_count", 0),
            "standard_ref": matrix.get("standard_ref", ""),
            "risk_factors": matrix.get("risk_factors", []),
        },
    }


def _copy_all(findings) -> str:
    """발견 전체의 수정 프롬프트를 한 번에 복사하기 위한 텍스트(TDD §3)."""
    lines = []
    for n, f in enumerate((f for f in findings if f.fix_prompt), start=1):
        lines.append(f"{n}. [{_location(f)}] {f.fix_prompt}")
    return "\n".join(lines)


def build_reports(scan, findings, sbom_rows, matrix, incomplete: bool,
                  grade_result=None, registry_incomplete: bool = False) -> tuple[dict, dict]:
    """개발자용·시민용 리포트를 조립한다. 저장은 호출부(파이프라인)가 병합해서 한다."""
    findings = list(findings)
    rows = [_finding_row(f) for f in findings]
    review_needed = sum(1 for f in findings if f.status == "review_needed")
    vulnerable = sum(1 for r in sbom_rows if (r or {}).get("cve_ids"))

    dev = {
        "grade": scan.grade,
        "disclaimer": DISCLAIMER,                    # 상시 표기 (G10)
        "upgrade": _upgrade(scan.grade, grade_result),
        "provenance": {
            "content_fingerprint": scan.content_fingerprint,
            "fingerprint_type": scan.fingerprint_type,
            "rule_catalog_version": scan.rule_catalog_version,
            "llm_model_id": scan.llm_model_id,       # judge 스킵 시 null
            "vuln_db_snapshot_date": scan.vuln_db_snapshot_date,
            "vuln_match_incomplete": bool(incomplete),   # OSV 부분 결과 → "일부 미대조"
            "registry_lookup_incomplete": bool(registry_incomplete),   # SCA-05·07 입력 미조회
        },
        "six_principles": _six_principles(findings),
        "findings": rows,
        "review_needed_count": review_needed,
        "sbom_summary": {"component_count": len(sbom_rows), "vulnerable_count": vulnerable},
        "supply_chain": _supply_chain(scan, matrix),
        "copy_all_fix_prompts": _copy_all(findings),
    }

    easy = {
        "grade": scan.grade,
        "disclaimer": DISCLAIMER,
        "easy_descriptions": [f.easy_description for f in findings if f.easy_description],
        "review_needed_count": review_needed,
    }

    log.info("리포트 조립", extra={"scan_id": str(scan.id), "findings": len(rows),
                                   "review_needed": review_needed,
                                   "vuln_match_incomplete": bool(incomplete)})
    return dev, easy
