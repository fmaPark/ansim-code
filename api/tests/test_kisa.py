import io
import json
import zipfile
from pathlib import Path

import pytest

from app.config import settings
from app.engine.kisa import kisa_snapshot_date, load_kisa

REPO_CSV = Path(__file__).resolve().parents[2] / "data" / "kisa" / "krcert_notices.csv"


def test_cve_extraction_from_any_column(tmp_path):
    csv = tmp_path / "k.csv"
    csv.write_text("제목,본문,링크\n"
                   "OpenSSL 보안 업데이트 권고,CVE-2024-12345 및 CVE-2024-99999 조치,https://boho.or.kr/1\n",
                   encoding="utf-8")
    notices = load_kisa(csv)
    assert "CVE-2024-12345" in notices and notices["CVE-2024-12345"].url == "https://boho.or.kr/1"
    assert notices["CVE-2024-99999"].title == "OpenSSL 보안 업데이트 권고"


def test_cp949_encoding_fallback(tmp_path):
    csv = tmp_path / "k.csv"
    csv.write_bytes("제목,본문,링크\n보안공지,CVE-2021-44228 조치 권고,https://boho.or.kr/2\n"
                    .encode("cp949"))          # data.go.kr 배포본이 EUC-KR인 경우 대비
    notices = load_kisa(csv)
    assert notices["CVE-2021-44228"].title == "보안공지"


def test_rows_without_cve_are_ignored(tmp_path):
    csv = tmp_path / "k.csv"
    csv.write_text("제목,본문,링크\n일반 안내,CVE 없음,https://boho.or.kr/3\n", encoding="utf-8")
    assert load_kisa(csv) == {}


def test_repo_snapshot_loads(tmp_path):
    """동봉 스냅샷 로드 스모크 — 추출 CVE 수 > 0 (TDD §4.6 이미지 동봉)."""
    notices = load_kisa(REPO_CSV)
    assert len(notices) > 0
    flask = notices["CVE-2018-1000656"]
    assert flask.url.startswith("https://") and flask.date == "2018-08-27"


def test_snapshot_date_file():
    assert kisa_snapshot_date(settings.kisa_csv_path) == "2026-08-29"


# ── 파이프라인 교차: OSV CVE ∩ KISA 공지 → SCA-03 ────────────────────────────

def _vulnerable_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("app/requirements.txt", "flask==0.12\n")
        z.writestr("app/package.json", json.dumps({"dependencies": {"lodash": "4.17.15"}}))
    return buf.getvalue()


def _osv_stub(incomplete: bool = False):
    from app.engine.osv import OsvResult, VulnInfo

    async def _stub(purls, transport=None):
        vulns = {}
        for purl in purls:
            if purl.startswith("pkg:pypi/flask"):
                vulns[purl] = [VulnInfo(
                    id="GHSA-562c-5r94-xh97", cve_ids=["CVE-2018-1000656"],
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    severity="critical", fixed_version="0.12.3")]
            elif purl.startswith("pkg:npm/lodash"):
                vulns[purl] = [VulnInfo(
                    id="GHSA-p6mc-m468-83gg", cve_ids=["CVE-2020-8203"],
                    cvss_vector="CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:H/A:N",
                    severity="high", fixed_version="4.17.19")]
        return OsvResult(vulns=vulns, incomplete=incomplete)

    return _stub


@pytest.mark.asyncio
async def test_kisa_cross_creates_sca03_with_notice_link(client, monkeypatch):
    from app.models import Finding

    monkeypatch.setattr("app.engine.pipeline.query_osv", _osv_stub())
    r = await client.post("/api/scans", files={"file": ("v.zip", _vulnerable_zip(), "application/zip")})
    sid = r.json()["scan_id"]
    assert (await client.get(f"/api/scans/{sid}")).json()["status"] == "done"

    body = (await client.get(f"/api/scans/{sid}/sbom")).json()
    flask = next(c for c in body["components"] if c["component_name"] == "flask")
    assert flask["cve_ids"] == ["CVE-2018-1000656"]
    assert flask["cvss_base"] == 9.8 and flask["cvss_impact"] == 5.9
    assert flask["cvss_exploitability"] == 3.9 and flask["cvss_severity"] == "critical"
    kisa_entry = next(e for e in flask["vulnerability_db"] if e["source"] == "KISA")
    assert kisa_entry["notice_url"].startswith("https://")

    from app.db import SessionLocal
    from app.models import Scan
    with SessionLocal() as db:
        sca03 = db.query(Finding).filter(Finding.scan_id == sid, Finding.rule_id == "SCA-03").all()
        assert sca03 and "국내 보안공지 발령" in sca03[0].evidence
        assert sca03[0].status == "confirmed" and sca03[0].severity == "high"
        scan = db.get(Scan, sid)
        assert scan.vuln_db_snapshot_date.startswith("OSV@")
        assert "KISA-CSV@2026-08-29" in scan.vuln_db_snapshot_date


@pytest.mark.asyncio
async def test_kisa_cross_runs_even_when_osv_incomplete(client, monkeypatch):
    from app.models import Finding

    monkeypatch.setattr("app.engine.pipeline.query_osv", _osv_stub(incomplete=True))
    r = await client.post("/api/scans", files={"file": ("v.zip", _vulnerable_zip(), "application/zip")})
    sid = r.json()["scan_id"]
    assert (await client.get(f"/api/scans/{sid}")).json()["status"] == "done"

    from app.db import SessionLocal
    from app.models import Scan
    with SessionLocal() as db:
        assert db.query(Finding).filter(Finding.scan_id == sid, Finding.rule_id == "SCA-03").count() >= 1
        assert db.get(Scan, sid).report_json["osv_incomplete"] is True    # "일부 미대조"
