"""Task 17 — 등급 결정론(P0-3) 순수 함수 + 파이프라인 결정론 통합 (계획 Step 1·3)."""
import io
import zipfile

import pytest

from app.engine.grade import calc_grade

F = lambda i, r, st, sev="high": dict(id=i, rule_id=r, status=st, severity=sev)  # noqa: E731
C = lambda i, sev: dict(cve_id=i, cvss_severity=sev)  # noqa: E731


def test_secret_confirmed_is_danger():
    g = calc_grade([F(1, "SEC-01", "confirmed", "critical")], [])
    assert g.grade == "위험" and g.upgrade_target == "안심" and g.upgrade_count == 1


def test_review_needed_only_is_safe():        # LLM 경유가 등급에 기여 불가 (G3)
    g = calc_grade([F(1, "P2", "review_needed"), F(2, "P4", "review_needed")], [])
    assert g.grade == "안심"


def test_medium_cve_is_caution_low_ignored():
    assert calc_grade([], [C("CVE-1", "medium")]).grade == "주의"
    assert calc_grade([], [C("CVE-2", "low")]).grade == "안심"


def test_danger_upgrade_target_is_caution_when_other_confirmed_remain():
    g = calc_grade([F(1, "P6", "confirmed", "critical"),
                    F(2, "AUX-01", "confirmed", "high")], [])
    assert g.grade == "위험" and g.upgrade_target == "주의" and g.upgrade_count == 1


def test_determinism_same_input_same_grade():  # B3 DoD (TDD §9)
    inp = ([F(1, "AUX-02", "confirmed", "medium")], [C("CVE-3", "high")])
    assert all(calc_grade(*inp).grade == "주의" for _ in range(50))


# ── 파이프라인 결정론 통합 (계획 Step 3) ──────────────────────────────────────
# 동일 zip 2회 스캔, 실행 간 LLM 스텁 응답을 서로 다르게 → 지문·룰버전·등급 동일(B3).

_DEBUG_PY = "DEBUG = True\napp.run(debug=True)\n"          # AUX-02 (semgrep, confirmed)
_COLLECT_PY = 'user = {"phone": input(), "birth": input()}\n'  # P2 계열 트리거 후보


def _fixture_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("app/settings.py", _DEBUG_PY)
        z.writestr("app/collect.py", _COLLECT_PY)
    return buf.getvalue()


def _llm_stub(text: str):
    async def stub(scan, drafts, root, registry, client=None):
        for d in drafts:
            if d.status == "review_needed":
                d.judge_explanation = text          # 실행마다 다른 LLM 산출물
    return stub


@pytest.mark.asyncio
async def test_pipeline_grade_deterministic_across_llm_outputs(client, monkeypatch):
    from app.models import Scan
    from app.db import SessionLocal

    payload = _fixture_zip()
    results = []
    for stub_text in ("첫 번째 실행의 판정 설명", "두 번째 실행은 전혀 다른 텍스트"):
        monkeypatch.setattr("app.engine.analysis.run_llm_stage", _llm_stub(stub_text))
        r = await client.post("/api/scans", files={"file": ("app.zip", payload, "application/zip")})
        assert r.status_code == 202
        scan_id = r.json()["scan_id"]
        db = SessionLocal()
        try:
            scan = db.get(Scan, scan_id)
            assert scan.status == "done", scan.error_message
            results.append((scan.content_fingerprint, scan.rule_catalog_version, scan.grade))
        finally:
            db.close()

    (fp1, rv1, g1), (fp2, rv2, g2) = results
    assert fp1 == fp2 and rv1 == rv2          # 같은 입력 (콘텐츠 지문·룰 버전)
    assert g1 == g2                            # → 같은 등급 (P0-3)
    assert g1 == "주의"                        # AUX-02 confirmed → 주의
