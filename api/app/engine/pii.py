"""한국형 PII — 주민등록번호 체크섬 + confirmed/review_needed 분기 (Task 13).

TDD §4.5: 가중치 (2,3,4,5,6,7,8,9,2,3,4,5) → 합 mod 11 → (11−나머지) mod 10 == 검증번호.
§11 항목 4(2026-08-29 사용자 확정): 무효 13자리는 review_needed 기본값 —
2020-10 이후 발급분은 체크섬 미적용이라 무효≠오탐. 기획 확정 시 상수 1곳 변경.
"""
import re

from app.engine.findings import FindingDraft
from app.engine.gitleaks_runner import RawSecret

WEIGHTS = (2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5)

# §11 항목 4 기본값 — 기획 확정 시 이 상수 1곳만 변경한다.
RRN_INVALID_STATUS = "review_needed"
RRN_INVALID_NOTE = "주민등록번호 형식 값, 검증 불가(2020-10 이후 발급분은 체크섬 미적용)"

# 카탈로그 표(Task 2)의 severity_default — 러너 로컬 상수(카탈로그와 1:1, test로 고정)
_SEVERITY = {"SEC-01": "critical", "SEC-02": "high", "SEC-03": "critical",
             "SEC-04": "critical", "SEC-05": "critical"}

_RRN_SHAPE = re.compile(r"^\d{6}[-\s]?[1-4]\d{6}$")


def validate_rrn(candidate: str) -> bool:
    digits = re.sub(r"\D", "", candidate)
    if len(digits) != 13:
        return False
    s = sum(int(d) * w for d, w in zip(digits[:12], WEIGHTS))
    return (11 - s % 11) % 10 == int(digits[12])


def _mask_evidence(raw: RawSecret) -> str:
    """Task 14 전까지의 최소 마스킹 — 파이프라인 통합 시 MaskRegistry가 대체 적용."""
    if not raw.secret_value:
        return raw.match
    return raw.match.replace(raw.secret_value, "****")


def classify_secret(raw: RawSecret) -> FindingDraft:
    """SEC-05 주민번호: 체크섬 유효→confirmed / 무효 13자리→review_needed.
    휴대전화·계좌번호→review_needed(Task 2 표 가정). 그 외 SEC-01~04→confirmed."""
    if raw.rule_id == "SEC-05":
        if _RRN_SHAPE.match(raw.secret_value.strip()):
            status = "confirmed" if validate_rrn(raw.secret_value) else RRN_INVALID_STATUS
        else:
            status = "review_needed"   # 휴대전화·계좌번호 패턴 — 오탐로 '위험' 남발 방지
    else:
        status = "confirmed"
    return FindingDraft(
        rule_id=raw.rule_id,
        severity=_SEVERITY.get(raw.rule_id, "high"),
        file_path=raw.file,
        line=raw.line,
        evidence=_mask_evidence(raw),
        status=status,
        grade_blocking=False,          # 등급 계산(Task 17)이 확정 — 여기선 기본값
    )
