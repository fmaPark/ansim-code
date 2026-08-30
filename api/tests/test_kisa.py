import io
import json
import zipfile
from pathlib import Path

import pytest

from app.engine.kisa import NOTICE_BOARD_URL, kisa_snapshot_date, load_kisa

REPO_CSV = Path(__file__).resolve().parents[2] / "data" / "kisa" / "krcert_notices.csv"

# data.go.kr/15155789 배포본의 실제 헤더 — 본문·링크 컬럼이 없다.
REAL_HEADER = "순번,게시판 종류,게시판 제목,작성자,작성일,조회수\n"


def _write(tmp_path, text: str, encoding: str = "utf-8") -> Path:
    csv = tmp_path / "k.csv"
    csv.write_bytes(text.encode(encoding))
    return csv


# ── 로더: 컬럼 판별 ──────────────────────────────────────────────────────────

def test_header_mapping_picks_title_not_row_number(tmp_path):
    """실배포본 스키마 — 제목 컬럼을 헤더로 찾는다(순번이 제목으로 잡히면 안 된다)."""
    csv = _write(tmp_path, REAL_HEADER +
                 "6269,취약점 정보,CVE-2024-22768 | Hitron Systems DVR 취약점,취약점분석팀,2024-01-30,527720\n")
    notice = load_kisa(csv).by_cve["CVE-2024-22768"]
    assert notice.title == "CVE-2024-22768 | Hitron Systems DVR 취약점"
    assert notice.date == "2024-01-30" and notice.board == "취약점 정보"
    assert notice.url == NOTICE_BOARD_URL          # 배포본에 링크 컬럼이 없다


def test_author_column_is_never_loaded(tmp_path):
    """`작성자`는 KISA 담당자 실명이다 — 어떤 필드에도 실리면 안 된다(개인정보)."""
    csv = _write(tmp_path, REAL_HEADER +
                 "6277,보안공지,기업 문자발송 시스템 해킹 주의(CVE-2024-11111),홍길동,2024-01-31,77976\n")
    snapshot = load_kisa(csv)
    loaded = list(snapshot.by_cve.values()) + snapshot.advisories
    assert loaded
    assert not any("홍길동" in f"{n.title} {n.url} {n.date} {n.board}" for n in loaded)


def test_cve_extraction_from_any_column(tmp_path):
    """본문·링크가 있는 배포본이 오면 그쪽 CVE도 잡는다(컬럼 구성 비의존)."""
    csv = _write(tmp_path, "제목,본문,링크\n"
                 "OpenSSL 보안 업데이트 권고,CVE-2024-12345 및 CVE-2024-99999 조치,https://boho.or.kr/1\n")
    notices = load_kisa(csv).by_cve
    assert notices["CVE-2024-12345"].url == "https://boho.or.kr/1"
    assert notices["CVE-2024-99999"].title == "OpenSSL 보안 업데이트 권고"


def test_cp949_encoding_fallback(tmp_path):
    """data.go.kr 배포본은 실제로 cp949다."""
    csv = _write(tmp_path, "제목,본문,링크\n보안공지,CVE-2021-44228 조치 권고,https://boho.or.kr/2\n",
                 encoding="cp949")
    assert load_kisa(csv).by_cve["CVE-2021-44228"].title == "보안공지"


def test_fallback_without_header_skips_numeric_cells(tmp_path):
    """헤더가 없으면 형태로 판별한다 — 순번·조회수는 제목 후보가 아니다."""
    csv = _write(tmp_path,
                 "6269,취약점 정보,CVE-2024-22768 | Hitron Systems DVR 취약점,2024-01-30,527720\n")
    notice = load_kisa(csv).by_cve["CVE-2024-22768"]
    assert notice.title == "CVE-2024-22768 | Hitron Systems DVR 취약점"
    assert notice.date == "2024-01-30"


def test_rows_without_cve_are_not_indexed(tmp_path):
    csv = _write(tmp_path, "제목,본문,링크\n일반 안내,CVE 없음,https://boho.or.kr/3\n")
    assert load_kisa(csv).by_cve == {}


def test_missing_file_returns_empty_snapshot(tmp_path):
    snapshot = load_kisa(tmp_path / "없는파일.csv")
    assert not snapshot and snapshot.by_cve == {} and snapshot.advisories == []


# ── 로더: 동봉 실데이터 스냅샷 (data.go.kr/15155789, 2025-12-04) ──────────────

def test_repo_snapshot_loads_real_distribution():
    snapshot = load_kisa(REPO_CSV)
    assert len(snapshot.by_cve) == 192              # 제목에 CVE가 실린 행에서만 추출된다
    assert len(snapshot.advisories) == 2316         # 보안공지 게시판 행
    assert not any(n.title.isdigit() for n in snapshot.by_cve.values())

    notice = snapshot.by_cve["CVE-2024-22768"]
    assert notice.title.startswith("CVE-2024-22768 | Hitron Systems DVR HVR-4781")
    assert notice.date == "2024-01-30" and notice.board == "취약점 정보"
    assert notice.url == NOTICE_BOARD_URL


def test_repo_snapshot_has_no_staff_names():
    """실데이터 회귀 가드 — 배포본 `작성자` 실명이 스냅샷에 유입되지 않는다."""
    snapshot = load_kisa(REPO_CSV)
    blob = " ".join(f"{n.title} {n.board}" for n in snapshot.advisories)
    assert not any(name in blob for name in ("신우성", "고은혜", "김대식"))


def test_product_match_against_real_snapshot():
    """2차 교차 — 보안공지 제목의 제품명 ↔ 컴포넌트명."""
    snapshot = load_kisa(REPO_CSV)
    assert snapshot.match_product("django").title == "Django 제품 보안 업데이트 권고"
    assert "aiohttp" in snapshot.match_product("aiohttp").title
    assert snapshot.match_product("Django").date == "2025-09-05"     # 최신 공지 선택


@pytest.mark.parametrize("name", [
    "flask", "lodash", "requests",     # 실데이터에 국내 보안공지가 없는 컴포넌트
    "six", "ab",                       # 3글자 이하 — "Six AD Practice" 오탐 차단
    "core", "@babel/core",             # 일반 명사 — "XML Core Services" 오탐 차단
])
def test_product_match_rejects_false_positives(name):
    assert load_kisa(REPO_CSV).match_product(name) is None


def test_snapshot_date_file():
    assert kisa_snapshot_date(REPO_CSV) == "2025-12-04"


# ── 파이프라인 교차 ──────────────────────────────────────────────────────────

def _zip(requirements: str, package_json: dict | None = None) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("app/requirements.txt", requirements)
        if package_json is not None:
            z.writestr("app/package.json", json.dumps(package_json))
    return buf.getvalue()


def _osv_stub(mapping: dict[str, tuple[str, str, str]], incomplete: bool = False):
    """{purl 접두사: (GHSA, CVE, fixed)} → OSV 응답 스텁."""
    from app.engine.osv import OsvResult, VulnInfo

    async def _stub(purls, transport=None):
        vulns = {}
        for purl in purls:
            for prefix, (ghsa, cve, fixed) in mapping.items():
                if purl.lower().startswith(prefix):
                    vulns[purl] = [VulnInfo(
                        id=ghsa, cve_ids=[cve],
                        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                        severity="critical", fixed_version=fixed)]
        return OsvResult(vulns=vulns, incomplete=incomplete)

    return _stub


_DJANGO_OSV = {"pkg:pypi/django": ("GHSA-2gwj-7jmv-h26r", "CVE-2022-28346", "3.2.13")}


def _use_repo_snapshot(monkeypatch):
    """이미지에 구워진 /srv/data 대신 저장소 스냅샷을 쓴다(이미지 재빌드 무관)."""
    monkeypatch.setattr("app.engine.pipeline.load_kisa", lambda *a, **k: load_kisa(REPO_CSV))


async def _scan(client, payload: bytes) -> str:
    r = await client.post("/api/scans", files={"file": ("v.zip", payload, "application/zip")})
    scan_id = r.json()["scan_id"]
    assert (await client.get(f"/api/scans/{scan_id}")).json()["status"] == "done"
    return scan_id


@pytest.mark.asyncio
async def test_cve_cross_creates_sca03_and_records_kisa_source(client, monkeypatch, tmp_path):
    """1차 경로 — 공지 CVE ∩ OSV CVE. 취약점별 출처(⑩)에 KISA가 남는다."""
    from app.models import Finding

    csv = _write(tmp_path, "제목,게시일,링크,본문\n"
                 "Flask 보안 업데이트 권고,2018-08-27,https://knvd.krcert.or.kr/info/vuln/notice,"
                 "CVE-2018-1000656 조치 권고\n")
    monkeypatch.setattr("app.engine.pipeline.load_kisa", lambda *a, **k: load_kisa(csv))
    monkeypatch.setattr("app.engine.pipeline.query_osv", _osv_stub(
        {"pkg:pypi/flask": ("GHSA-562c-5r94-xh97", "CVE-2018-1000656", "0.12.3")}))

    scan_id = await _scan(client, _zip("flask==0.12\n"))

    body = (await client.get(f"/api/scans/{scan_id}/sbom")).json()
    flask = next(c for c in body["components"] if c["component_name"].lower() == "flask")
    kisa_entry = next(e for e in flask["vulnerability_db"] if e["source"] == "KISA")
    assert kisa_entry["notice_url"].startswith("https://") and kisa_entry["match"] == "cve"

    from app.db import SessionLocal
    with SessionLocal() as db:
        sca03 = db.query(Finding).filter(Finding.scan_id == scan_id,
                                         Finding.rule_id == "SCA-03").all()
    assert sca03 and "국내 보안공지 발령(CVE 교차)" in sca03[0].evidence
    assert sca03[0].status == "confirmed" and sca03[0].severity == "high"


@pytest.mark.asyncio
async def test_product_cross_creates_sca03_without_kisa_source(client, monkeypatch):
    """2차 경로 — 실데이터 스냅샷의 Django 보안공지 ↔ django 컴포넌트.

    KISA가 그 CVE를 발령한 것은 아니므로 취약점별 출처에는 넣지 않는다.
    """
    from app.db import SessionLocal
    from app.models import Finding, Scan
    from app.engine.kisa import kisa_snapshot_label

    _use_repo_snapshot(monkeypatch)
    monkeypatch.setattr("app.engine.pipeline.query_osv", _osv_stub(_DJANGO_OSV))

    scan_id = await _scan(client, _zip("Django==3.2.12\n"))

    body = (await client.get(f"/api/scans/{scan_id}/sbom")).json()
    django = next(c for c in body["components"] if c["component_name"].lower() == "django")
    assert django["cve_ids"] == ["CVE-2022-28346"]
    assert not [e for e in (django["vulnerability_db"] or []) if e["source"] == "KISA"]

    with SessionLocal() as db:
        sca03 = db.query(Finding).filter(Finding.scan_id == scan_id,
                                         Finding.rule_id == "SCA-03").all()
        scan = db.get(Scan, scan_id)
    assert len(sca03) == 1
    assert "국내 보안공지 발령(제품명 일치)" in sca03[0].evidence
    assert "Django 제품 보안 업데이트 권고" in sca03[0].evidence
    assert len(sca03[0].evidence) < 400        # CVE 26건이 통째로 실리면 안 된다(UI 카드)
    assert sca03[0].status == "confirmed" and sca03[0].severity == "high"
    assert scan.vuln_db_snapshot_date.startswith("OSV@")
    assert kisa_snapshot_label() in scan.vuln_db_snapshot_date


@pytest.mark.asyncio
async def test_product_cross_evidence_truncates_cve_list(client, monkeypatch):
    """실제 Django는 OSV CVE가 26건까지 나온다 — evidence에 전량 나열하면 안 된다."""
    from app.db import SessionLocal
    from app.engine.osv import OsvResult, VulnInfo
    from app.models import Finding

    cves = [f"CVE-2022-2834{i}" for i in range(6)]

    async def _many(purls, transport=None):
        return OsvResult(vulns={p: [VulnInfo(id=f"GHSA-{i}", cve_ids=[c], cvss_vector=None,
                                             severity="high", fixed_version="3.2.13")
                                    for i, c in enumerate(cves)]
                                for p in purls if p.lower().startswith("pkg:pypi/django")},
                         incomplete=False)

    _use_repo_snapshot(monkeypatch)
    monkeypatch.setattr("app.engine.pipeline.query_osv", _many)

    scan_id = await _scan(client, _zip("Django==3.2.12\n"))

    with SessionLocal() as db:
        evidence = db.query(Finding).filter(Finding.scan_id == scan_id,
                                            Finding.rule_id == "SCA-03").one().evidence
    assert "외 3건" in evidence and evidence.count("CVE-") == 3


@pytest.mark.asyncio
async def test_product_cross_skipped_without_osv_cve(client, monkeypatch):
    """OSV가 취약 판정하지 않은 컴포넌트는 제품명이 겹쳐도 SCA-03을 만들지 않는다."""
    from app.db import SessionLocal
    from app.models import Finding

    _use_repo_snapshot(monkeypatch)
    monkeypatch.setattr("app.engine.pipeline.query_osv", _osv_stub({}))

    scan_id = await _scan(client, _zip("Django==3.2.12\nredis==4.5.0\n"))

    with SessionLocal() as db:
        assert db.query(Finding).filter(Finding.scan_id == scan_id,
                                        Finding.rule_id == "SCA-03").count() == 0


@pytest.mark.asyncio
async def test_kisa_cross_runs_even_when_osv_incomplete(client, monkeypatch):
    from app.db import SessionLocal
    from app.models import Finding, Scan

    _use_repo_snapshot(monkeypatch)
    monkeypatch.setattr("app.engine.pipeline.query_osv",
                        _osv_stub(_DJANGO_OSV, incomplete=True))

    scan_id = await _scan(client, _zip("Django==3.2.12\n"))

    with SessionLocal() as db:
        assert db.query(Finding).filter(Finding.scan_id == scan_id,
                                        Finding.rule_id == "SCA-03").count() >= 1
        assert db.get(Scan, scan_id).report_json["osv_incomplete"] is True   # "일부 미대조"
