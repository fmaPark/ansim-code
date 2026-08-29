import subprocess

import pytest

from app.engine.ingest import IngestResult
from app.engine.pipeline import run_scan, upload_path

# ASGITransport는 응답을 돌려준 뒤 BackgroundTasks를 그 자리에서 실행한다.
# 따라서 POST가 반환된 시점에 run_scan은 이미 끝나 있고, 테스트가 run_scan을 다시
# 부르면 파기된 업로드를 두 번째로 읽는 셈이 된다 — 실행 전에 monkeypatch를 건다.

def _boom(*args, **kwargs):
    raise RuntimeError("boom")


async def _noop(*args, **kwargs):
    return None


@pytest.fixture
def local_repo(tmp_path):
    """ingest_git은 https만 허용하므로, git 경로 테스트는 로컬 clone으로 monkeypatch한다."""
    d = tmp_path / "repo"
    d.mkdir()
    (d / "main.py").write_text("import os\n")
    git = ["git", "-C", str(d), "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run(["git", "init", "-q", str(d)], check=True, capture_output=True)
    subprocess.run([*git, "add", "-A"], check=True, capture_output=True)
    subprocess.run([*git, "commit", "-qm", "init"], check=True, capture_output=True)
    return d


def _local_clone(url, workdir):
    dst = workdir / "repo"
    subprocess.run(["git", "clone", "--depth", "1", str(url), str(dst)],
                   check=True, capture_output=True)
    commit = subprocess.run(["git", "-C", str(dst), "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    return IngestResult(root=dst, commit_hash=commit)


def _row(database, scan_id):
    from sqlalchemy.orm import Session

    from app.models import Scan

    with Session(database) as db:
        return db.get(Scan, scan_id)


async def _post_zip(client, small_zip):
    r = await client.post("/api/scans", files={"file": ("a.zip", small_zip, "application/zip")})
    assert r.status_code == 202
    return r.json()["scan_id"]


@pytest.mark.asyncio
async def test_scan_lifecycle_zip(client, small_zip, database):
    sid = await _post_zip(client, small_zip)
    s = (await client.get(f"/api/scans/{sid}")).json()
    assert s["status"] == "done"
    assert s["status"] != "running"            # G12: 영원히 running 없음
    assert s["current_stage"] == "완료"

    row = _row(database, sid)                  # G11: 파기 전에 확정 기록된 재현성 앵커
    assert row.fingerprint_type == "tree_hash"
    assert len(row.content_fingerprint) == 64
    assert row.rule_catalog_version
    assert row.purged_at is not None


@pytest.mark.asyncio
async def test_scan_lifecycle_git(client, local_repo, monkeypatch, database):
    monkeypatch.setattr("app.engine.ingest.ingest_git", _local_clone)
    r = await client.post("/api/scans", json={"git_url": str(local_repo)})
    assert r.status_code == 202
    sid = r.json()["scan_id"]

    row = _row(database, sid)
    assert row.status == "done"
    assert row.fingerprint_type == "git_commit"
    expected = subprocess.run(["git", "-C", str(local_repo), "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
    assert row.content_fingerprint == expected


@pytest.mark.asyncio
async def test_pipeline_failure_sets_failed(client, small_zip, monkeypatch, database):
    monkeypatch.setattr("app.engine.pipeline.stage_ingest", _boom)
    sid = await _post_zip(client, small_zip)

    s = (await client.get(f"/api/scans/{sid}")).json()
    assert s["status"] == "failed"             # G12: 예외 시 failed로 확정
    assert "boom" in s["error_message"]
    assert _row(database, sid).purged_at is not None


@pytest.mark.asyncio
async def test_upload_original_purged_on_failure(client, small_zip, monkeypatch):
    """G1: 업로드 원본은 격리 워크스페이스 밖이라 파이프라인이 직접 파기해야 한다."""
    monkeypatch.setattr("app.routes.scans.run_scan", _noop)   # 파이프라인을 잠시 세워 둔다
    sid = await _post_zip(client, small_zip)
    assert upload_path(sid).exists()                          # 라우트가 워크스페이스 밖에 저장했다

    monkeypatch.setattr("app.engine.pipeline.stage_ingest", _boom)
    await run_scan(sid)
    assert not upload_path(sid).exists()                      # 실패 경로에서도 잔존 0


@pytest.mark.asyncio
async def test_get_unknown_scan_is_404(client):
    r = await client.get("/api/scans/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_unsupported_content_type_rejected(client):
    r = await client.post("/api/scans", content=b"x", headers={"content-type": "text/plain"})
    assert r.status_code == 415
