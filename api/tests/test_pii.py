"""Task 13 — 주민번호 체크섬 + confirmed/review_needed 분기 (TDD §4.5 · §11 항목 4)."""
from app.engine.pii import validate_rrn

WEIGHTS = (2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5)


def _make_valid(base12: str) -> str:      # 테스트 내 합성 — 실번호 미사용
    s = sum(int(d) * w for d, w in zip(base12, WEIGHTS))
    return base12 + str((11 - s % 11) % 10)


def test_valid_checksum_true():
    assert validate_rrn(_make_valid("900101123456"))


def test_invalid_checksum_false():
    rrn = _make_valid("900101123456")
    bad = rrn[:-1] + str((int(rrn[-1]) + 1) % 10)   # 검증번호 +1 mod 10 → 항상 무효
    assert not validate_rrn(bad)


def test_rrn_with_separator_and_short_input():
    v = _make_valid("900101123456")
    assert validate_rrn(v[:6] + "-" + v[6:])        # 하이픈 표기도 동일 판정
    assert not validate_rrn("900101-123456")        # 12자리는 판정 불가 → False


def test_classification_split():          # TDD §9 P0아님·Unit 요구
    from app.engine.gitleaks_runner import RawSecret
    from app.engine.pii import classify_secret

    valid = RawSecret("SEC-05", "a.py", 3, _make_valid("900101123456"), "rrn")
    invalid = RawSecret("SEC-05", "a.py", 4, _make_valid("900101123456")[:-1] + "0", "rrn")
    assert classify_secret(valid).status == "confirmed"        # → 등급 '위험' 트리거
    assert classify_secret(invalid).status == "review_needed"


def test_phone_account_always_review_needed():     # Task 2 표 가정(오탐로 '위험' 남발 방지)
    from app.engine.gitleaks_runner import RawSecret
    from app.engine.pii import classify_secret

    phone = RawSecret("SEC-05", "a.py", 5, "010-1234-5678", "phone = 010-1234-5678")
    assert classify_secret(phone).status == "review_needed"


def test_sec01_to_04_confirmed_and_evidence_masked():
    from app.engine.gitleaks_runner import RawSecret
    from app.engine.pii import classify_secret

    raw = RawSecret("SEC-04", "c.py", 1, "AKIAIOSFODNN7EXAMPLE", 'KEY = "AKIAIOSFODNN7EXAMPLE"')
    d = classify_secret(raw)
    assert d.status == "confirmed" and d.severity == "critical"
    assert "AKIAIOSFODNN7EXAMPLE" not in (d.evidence or "")     # G2: 원문 미저장


def test_test_path_secret_demoted_to_review_needed():
    """이슈 #29 — 테스트 경로의 합성 시크릿은 등급을 끌어내리지 않는다(목록에는 남는다)."""
    from app.engine.gitleaks_runner import RawSecret
    from app.engine.pii import classify_secret

    key = "AKIAIOSFODNN7EXAMPLE"
    for path in ("api/tests/test_gitleaks.py", "web/src/auth.test.ts", "pkg/foo_test.py"):
        d = classify_secret(RawSecret("SEC-04", path, 1, key, f'KEY = "{key}"'))
        assert d.status == "review_needed", path
        assert "테스트 경로" in d.evidence          # 강등 사유가 리포트에 남는다

    prod = classify_secret(RawSecret("SEC-04", "api/app/config.py", 1, key, f'KEY = "{key}"'))
    assert prod.status == "confirmed"               # 운영 경로는 그대로 위험 트리거


def test_test_path_demotion_does_not_promote():
    """이미 review_needed인 건은 그대로 — 강등은 confirmed에서만 일어난다."""
    from app.engine.gitleaks_runner import RawSecret
    from app.engine.pii import classify_secret

    phone = RawSecret("SEC-05", "api/tests/test_x.py", 5, "010-1234-5678", "phone = 010-1234-5678")
    assert classify_secret(phone).status == "review_needed"
