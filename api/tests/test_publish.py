"""Task 22 — 등급 공개 2단계(.ansimcode 소유 증명)·공개 페이지·SVG 배지 (TDD §4.4·§4.5, ADR v1.3 G10)."""
import subprocess
import uuid

import pytest

from app.engine.ingest import IngestResult


def _local_clone(url, workdir):
    dst = workdir / "repo"
    subprocess.run(["git", "clone", "--depth", "1", str(url), str(dst)],
                   check=True, capture_output=True)
    commit = subprocess.run(["git", "-C", str(dst), "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    return IngestResult(root=dst, commit_hash=commit)


@pytest.fixture
def local_repo(tmp_path):
    """소유 증명 대조용 로컬 저장소 — ingest_git은 https만 허용하므로 monkeypatch로 clone한다."""
    d = tmp_path / "repo"
    d.mkdir()
    (d / "main.py").write_text("import os\n")
    subprocess.run(["git", "init", "-q", str(d)], check=True, capture_output=True)
    _commit_all(d)
    return d


def _commit_all(repo):
    git = ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run([*git, "add", "-A"], check=True, capture_output=True)
    subprocess.run([*git, "commit", "-qm", "t"], check=True, capture_output=True)


def _seed_scan(database, **overrides):
    from app.db import SessionLocal
    from app.models import Scan

    fields = dict(
        source_type="git", source_ref="https://example.com/a.git", status="done",
        grade="주의", content_fingerprint="c" * 40, fingerprint_type="git_commit",
        rule_catalog_version="rcv-test", llm_model_id="gemini-3.5-flash-t",
        vuln_db_snapshot_date="OSV@2026-08-29; KISA-CSV@2025-12-04",
        easy_report_json={"grade": "주의", "disclaimer": "d",
                          "easy_descriptions": ["쉬운 설명"], "review_needed_count": 1},
    )
    fields.update(overrides)
    scan = Scan(**fields)
    with SessionLocal() as db:
        db.add(scan)
        db.commit()
        return scan.id


def _row(database, scan_id):
    from app.db import SessionLocal
    from app.models import Scan

    with SessionLocal() as db:
        return db.get(Scan, scan_id)


# ── 1단계·zip 차단 ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_zip_publish_rejected_403_with_notice(client, database):
    """G10: zip은 소유 증명 불가 — 403 + §11 항목 8 안내 문구."""
    from app.routes.public import ZIP_PUBLISH_NOTICE

    sid = _seed_scan(database, source_type="zip", source_ref="a.zip",
                     fingerprint_type="tree_hash")
    r = await client.post(f"/api/scans/{sid}/publish")
    assert r.status_code == 403
    assert r.json()["detail"] == ZIP_PUBLISH_NOTICE


@pytest.mark.asyncio
async def test_git_publish_step1_issues_token(client, database):
    sid = _seed_scan(database)
    r = await client.post(f"/api/scans/{sid}/publish")
    assert r.status_code == 200
    body = r.json()
    assert body["token"] and ".ansimcode" in body["instructions"]
    assert _row(database, sid).publish_token == body["token"]
    assert _row(database, sid).is_public is False              # 1단계는 공개 아님


@pytest.mark.asyncio
async def test_publish_requires_completed_scan(client, database):
    sid = _seed_scan(database, status="running", grade=None)
    r = await client.post(f"/api/scans/{sid}/publish")
    assert r.status_code == 409


# ── 2단계 소유 증명 ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_step2_token_mismatch_409(client, database, local_repo, monkeypatch):
    monkeypatch.setattr("app.engine.ingest.ingest_git", _local_clone)
    sid = _seed_scan(database, source_ref=str(local_repo), publish_token="expected-token")

    (local_repo / ".ansimcode").write_text("wrong-token\n")
    _commit_all(local_repo)

    r = await client.post(f"/api/scans/{sid}/publish", json={"confirm": True})
    assert r.status_code == 409
    assert _row(database, sid).is_public is False


@pytest.mark.asyncio
async def test_step2_success_publishes_and_serves_badge(client, database, local_repo, monkeypatch):
    monkeypatch.setattr("app.engine.ingest.ingest_git", _local_clone)
    sid = _seed_scan(database, source_ref=str(local_repo))

    token = (await client.post(f"/api/scans/{sid}/publish")).json()["token"]
    (local_repo / ".ansimcode").write_text(f"{token}\n")       # strip() 대조 확인용 개행
    _commit_all(local_repo)

    r = await client.post(f"/api/scans/{sid}/publish", json={"confirm": True})
    assert r.status_code == 200
    body = r.json()
    slug = body["public_url"].rsplit("/", 1)[-1]
    assert body["public_url"] == f"/g/{slug}"
    assert f"/api/public/badge/{slug}.svg" in body["badge_markdown"]
    row = _row(database, sid)
    assert row.is_public is True and row.public_slug == slug

    # 공개 페이지 데이터 — G11 4종 + 면책 고지(§11 항목 7)
    g = await client.get(f"/api/public/grades/{slug}")
    assert g.status_code == 200
    data = g.json()
    assert data["grade"] == "주의"
    assert data["easy_report"]["easy_descriptions"] == ["쉬운 설명"]
    prov = data["provenance"]
    assert prov["content_fingerprint"] and prov["rule_catalog_version"]
    assert prov["llm_model_id"] and prov["vuln_db_snapshot_date"]
    assert "자가점검" in data["disclaimer"]

    # SVG 배지 — 캐시 헤더 + ETag + 304 (TDD §4.4 GitHub camo 대응)
    b = await client.get(f"/api/public/badge/{slug}.svg")
    assert b.status_code == 200
    assert b.headers["content-type"].startswith("image/svg+xml")
    assert b.headers["cache-control"] == "max-age=300, must-revalidate"
    assert "주의" in b.text
    etag = b.headers["etag"]
    again = await client.get(f"/api/public/badge/{slug}.svg",
                             headers={"if-none-match": etag})
    assert again.status_code == 304


@pytest.mark.asyncio
async def test_public_endpoints_404_for_unknown_slug(client, database):
    assert (await client.get("/api/public/grades/nope")).status_code == 404
    assert (await client.get("/api/public/badge/nope.svg")).status_code == 404
    assert (await client.post(f"/api/scans/{uuid.uuid4()}/publish")).status_code == 404


# ── FE 계약 보강 — PublishFlow가 폴링 응답만으로 git/zip을 구분한다 ─────────

@pytest.mark.asyncio
async def test_scan_status_exposes_source_type(client, database):
    sid = _seed_scan(database)
    r = await client.get(f"/api/scans/{sid}")
    assert r.json()["source_type"] == "git"
