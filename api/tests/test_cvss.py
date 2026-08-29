from app.engine.cvss import derive_cvss3


def test_critical_vector():   # CVSS 3.1 스펙 예제값
    base, impact, expl, sev = derive_cvss3("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
    assert (base, impact, expl, sev) == (9.8, 5.9, 3.9, "critical")


def test_medium_vector():
    base, *_, sev = derive_cvss3("CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N")
    assert sev == "medium" and 4.0 <= base < 7.0


def test_plan_sample_vector_is_actually_low():
    """계획서 Step 1의 'medium' 예시 벡터는 스펙상 3.7(Low)이다 — 스펙을 따른다.

    AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:N → Exploitability 1.2 · Impact 2.5 · Base 3.7.
    계획의 기대값(medium)이 아니라 CVSS v3.1 공식 결과를 정답으로 삼았다.
    """
    base, _impact, _expl, sev = derive_cvss3("CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:N")
    assert (base, sev) == (3.7, "low")


def test_missing_vector_returns_none():
    assert derive_cvss3(None) is None        # → cvss_null_reason="벡터 미제공"


def test_scope_changed_vector():
    base, impact, expl, sev = derive_cvss3("CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:L/I:L/A:N")
    assert sev == "medium" and base == 6.4    # 스펙 예제 (CVE-2013-6014 형태)


def test_no_impact_is_zero():
    base, _impact, _expl, sev = derive_cvss3("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N")
    assert base == 0.0 and sev == "low"


def test_non_cvss3_vector_returns_none():
    assert derive_cvss3("CVSS:2.0/AV:N/AC:L/Au:N/C:P/I:P/A:P") is None
