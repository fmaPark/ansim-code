"""Task 19 — 이중 리포트 조립 + /report API.

JSON 키는 프론트(S5)와의 계약이다 — 계획 문서 Task 19의 구조를 그대로 단언한다.
"""
import io
import uuid
import zipfile
from types import SimpleNamespace

import pytest

from app.report.builder import DISCLAIMER, build_reports


def finding(i, rule_id="AUX-02", status="confirmed", severity="medium",
            file_path="settings.py", line=12, blocking=False):
    return SimpleNamespace(
        id=i, rule_id=rule_id, severity=severity, status=status, file_path=file_path,
        line=line, evidence='DEBUG = True', grade_blocking=blocking,
        judge_explanation=None, judge_evidence_lines=None,
        fix_prompt=f"수정 지시 {i}", easy_description=f"쉬운 설명 {i}")


def scan_stub(grade="주의", **kw):
    base = dict(id=uuid.uuid4(), grade=grade, content_fingerprint="abc123",
                fingerprint_type="git_commit", rule_catalog_version="ver1",
                llm_model_id=None, vuln_db_snapshot_date="OSV@2026-08-27; KISA-CSV@2026-08-29",
                supply_chain_class="오픈소스", report_json={}, easy_report_json=None)
    base.update(kw)
    return SimpleNamespace(**base)


MATRIX = {"standard_ref": "TTAK.KO-11.0322 §5.1.2 표 5-1", "supply_chain_class": "오픈소스",
          "component_count": 12,
          "risk_factors": [{"name": "라이선스 위반", "component_count": 1},
                           {"name": "취약점 전파", "component_count": 2}]}

SBOM_ROWS = [{"component_name": f"pkg{i}", "cve_ids": ["CVE-1"] if i < 2 else []}
             for i in range(12)]


def test_every_finding_carries_standard_ref():
    """개발자용 리포트는 조항 인용 리포트다 — 발견마다 근거 조항이 있어야 한다."""
    findings = [finding(1, "AUX-02"), finding(2, "P9", file_path=None, line=None),
                finding(3, "SEC-01", severity="critical")]
    dev, _ = build_reports(scan_stub(), findings, SBOM_ROWS, MATRIX, incomplete=False)

    assert len(dev["findings"]) == 3
    assert all(f["standard_ref"] for f in dev["findings"])
    assert all(f["title"] for f in dev["findings"])


def test_safe_grade_reports_review_needed_count():
    """confirmed 0 + review_needed >0 → 안심 + '검토 필요 n건' 병기 (TDD §4.5)."""
    findings = [finding(i, "P2", status="review_needed") for i in (1, 2, 3, 4)]
    dev, easy = build_reports(scan_stub(grade="안심"), findings, [], MATRIX, incomplete=False)

    assert dev["grade"] == "안심"
    assert dev["review_needed_count"] == 4
    assert dev["upgrade"] is None                 # 안심이면 상향 블록 없음
    assert easy["review_needed_count"] == 4


def test_upgrade_block_lists_blocking_ids():
    findings = [finding(1, "SEC-01", severity="critical", blocking=True),
                finding(7, "AUX-01", severity="high", blocking=True),
                finding(9, "AUX-03", status="confirmed")]
    grade_result = SimpleNamespace(upgrade_target="주의", upgrade_count=2,
                                   blocking_finding_ids=[1, 7], blocking_cve_ids=[])
    dev, _ = build_reports(scan_stub(grade="위험"), findings, [], MATRIX,
                           incomplete=False, grade_result=grade_result)

    assert dev["upgrade"]["target"] == "주의"
    assert dev["upgrade"]["count"] == 2
    assert dev["upgrade"]["blocking_finding_ids"] == [1, 7]
    assert "주의" in dev["upgrade"]["message"]


def test_incomplete_osv_sets_provenance_flag():
    dev, _ = build_reports(scan_stub(), [finding(1)], SBOM_ROWS, MATRIX, incomplete=True)

    p = dev["provenance"]
    assert p["vuln_match_incomplete"] is True
    assert p["content_fingerprint"] == "abc123" and p["fingerprint_type"] == "git_commit"
    assert p["rule_catalog_version"] == "ver1"
    assert p["llm_model_id"] is None              # judge 스킵 시 null 허용
    assert "OSV@" in p["vuln_db_snapshot_date"]


def test_copy_all_joins_every_fix_prompt():
    findings = [finding(1), finding(2, file_path="a.py", line=5)]
    dev, _ = build_reports(scan_stub(), findings, [], MATRIX, incomplete=False)

    text = dev["copy_all_fix_prompts"]
    assert "수정 지시 1" in text and "수정 지시 2" in text
    assert "[settings.py:12]" in text and "[a.py:5]" in text


def test_six_principles_axes_and_counts():
    findings = [finding(1, "P2", status="review_needed"), finding(2, "P6", severity="critical"),
                finding(3, "P9", file_path=None, line=None)]
    dev, _ = build_reports(scan_stub(), findings, [], MATRIX, incomplete=False)

    axes = {a["principle"]: a for a in dev["six_principles"]}
    assert list(axes) == ["적법성", "안전성", "투명성", "참여성", "책임성", "공정성"]
    assert axes["적법성"]["finding_count"] == 1          # P2
    assert axes["안전성"]["finding_count"] == 1          # P6
    assert axes["투명성"]["finding_count"] == 1          # P9
    assert axes["참여성"]["note"] and axes["공정성"]["note"]   # 자동 진단 범위 밖 안내


def test_disclaimer_present_in_both_reports():
    dev, easy = build_reports(scan_stub(), [finding(1)], [], MATRIX, incomplete=False)
    assert dev["disclaimer"] == DISCLAIMER == easy["disclaimer"]
    assert "인증이 아닌 자가점검 보조" in DISCLAIMER


def test_supply_chain_matrix_contract_shape():
    dev, _ = build_reports(scan_stub(), [], SBOM_ROWS, MATRIX, incomplete=False)

    sc = dev["supply_chain"]
    assert sc["class"] == "오픈소스"
    assert sc["matrix"]["위험요인"] == ["라이선스 위반", "취약점 전파"]
    assert sc["matrix"]["component_count"] == 12
    assert dev["sbom_summary"] == {"component_count": 12, "vulnerable_count": 2}


def test_easy_report_carries_only_citizen_fields():
    findings = [finding(1), finding(2, "P2", status="review_needed")]
    _, easy = build_reports(scan_stub(), findings, [], MATRIX, incomplete=False)

    assert set(easy) == {"grade", "disclaimer", "easy_descriptions", "review_needed_count"}
    assert easy["easy_descriptions"] == ["쉬운 설명 1", "쉬운 설명 2"]


# ── API + 파이프라인 통합 ────────────────────────────────────────────────────

_DEBUG_ZIP_SRC = "DEBUG = True\napp.run(debug=True)\n"


def _zip_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("app/settings.py", _DEBUG_ZIP_SRC)
        z.writestr("requirements.txt", "flask==2.0.0\n")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_report_endpoint_returns_dev_and_easy(client):
    r = await client.post("/api/scans",
                          files={"file": ("app.zip", _zip_bytes(), "application/zip")})
    scan_id = r.json()["scan_id"]

    dev = await client.get(f"/api/scans/{scan_id}/report")
    assert dev.status_code == 200
    body = dev.json()
    assert body["grade"] in {"안심", "주의", "위험"}
    assert body["disclaimer"] == DISCLAIMER
    assert all(f["standard_ref"] for f in body["findings"])
    assert all(f["fix_prompt"] and f["easy_description"] for f in body["findings"])

    easy = await client.get(f"/api/scans/{scan_id}/report?mode=easy")
    assert easy.status_code == 200
    assert set(easy.json()) == {"grade", "disclaimer", "easy_descriptions", "review_needed_count"}


@pytest.mark.asyncio
async def test_report_preserves_scratch_keys_for_sbom_endpoint(client):
    """report_json은 병합 저장 — parse_markers·osv_incomplete·matrix_0322가 살아있어야 한다."""
    r = await client.post("/api/scans",
                          files={"file": ("app.zip", _zip_bytes(), "application/zip")})
    scan_id = r.json()["scan_id"]

    sbom = await client.get(f"/api/scans/{scan_id}/sbom")
    assert sbom.status_code == 200
    assert "parse_markers" in sbom.json()

    from app.db import SessionLocal
    from app.models import Scan
    with SessionLocal() as db:
        stored = db.get(Scan, uuid.UUID(scan_id)).report_json
    assert "matrix_0322" in stored and "osv_incomplete" in stored
    assert stored["grade"] and stored["six_principles"]


@pytest.mark.asyncio
async def test_report_404_and_409(client):
    missing = await client.get(f"/api/scans/{uuid.uuid4()}/report")
    assert missing.status_code == 404

    from app.db import SessionLocal
    from app.models import Scan
    pending = Scan(source_type="git", source_ref="https://example.com/x.git", status="running")
    with SessionLocal() as db:
        db.add(pending)
        db.commit()
        pending_id = pending.id
    r = await client.get(f"/api/scans/{pending_id}/report")
    assert r.status_code == 409       # done 이전엔 리포트 없음
