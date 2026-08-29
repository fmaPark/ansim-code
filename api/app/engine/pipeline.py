import asyncio
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.db import SessionLocal
from app.engine import analysis
from app.engine import fingerprint as fp
from app.engine import ingest as ing
from app.engine.catalog import rule_catalog_version
from app.engine.workspace import scan_workspace
from app.models import Scan

log = logging.getLogger(__name__)


def upload_path(scan_id) -> Path:
    return Path(settings.upload_dir) / f"{scan_id}.zip"


def purge_upload(scan_id) -> None:
    """G1: 업로드 원본은 격리 워크스페이스 밖이라 workspace의 cleanup이 닿지 않는다."""
    try:
        upload_path(scan_id).unlink(missing_ok=True)
    except OSError:
        log.error("upload purge failed", extra={"scan_id": str(scan_id)})


def purge_orphan_uploads() -> None:
    """기동 시 잔존 업로드 정리 — uvicorn 단일 워커·in-process 전제라 살아있는 스캔이 없다."""
    d = Path(settings.upload_dir)
    if not d.is_dir():
        return
    for f in d.iterdir():
        if f.is_file():
            f.unlink(missing_ok=True)


def _set(db, scan, **kw):
    for k, v in kw.items():
        setattr(scan, k, v)
    db.commit()


def stage_ingest(scan, ws):
    if scan.source_type == "git":
        return ing.ingest_git(scan.source_ref, ws)
    return ing.ingest_zip(upload_path(scan.id), ws)


async def run_scan(scan_id):
    scan_id = uuid.UUID(str(scan_id))
    db = SessionLocal()
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            log.error("scan not found", extra={"scan_id": str(scan_id)})
            return
        started = time.monotonic()
        try:
            async with asyncio.timeout(settings.scan_timeout_seconds):   # G12 전체 타임아웃
                _set(db, scan, status="running", current_stage="환경분석")   # §11.1
                with scan_workspace(on_purged=lambda: _set(db, scan, purged_at=datetime.utcnow())) as ws:
                    res = await asyncio.to_thread(stage_ingest, scan, ws)
                    _set(db, scan,
                         content_fingerprint=res.commit_hash or fp.tree_fingerprint(res.root),
                         fingerprint_type="git_commit" if res.commit_hash else "tree_hash",
                         rule_catalog_version=rule_catalog_version())     # G11: 파기 전 확정
                    _set(db, scan, current_stage="현황진단")   # §11.2 — Task 6~8
                    _set(db, scan, current_stage="위험분석")   # §11.3 — Task 9~17
                    # M4: 정적 룰(gitleaks·semgrep·repo_checks) + 마스킹(P0-2) — Task 12~15
                    drafts, registry = await asyncio.to_thread(analysis.run_static_stage, res.root)
                    # M4: LLM judge — P1·P4 합성 + 스니펫(파기 전) + 12 병렬, status 불변(G3)
                    await analysis.run_llm_stage(scan, drafts, res.root, registry)
                    analysis.persist_findings(db, scan.id, drafts)
                    _set(db, scan, current_stage="대책수립")   # §11.4 — Task 18~19
                _set(db, scan, status="done", current_stage="완료")
        except Exception as e:
            # TimeoutError처럼 str(e)가 빈 예외가 있어 타입명을 함께 남긴다.
            log.exception("scan failed", extra={"scan_id": str(scan_id)})
            _set(db, scan, status="failed", error_message=f"{type(e).__name__}: {e}"[:500])   # G12
        log.info("scan finished", extra={"scan_id": str(scan_id), "status": scan.status,
                                         "duration_ms": round((time.monotonic() - started) * 1000)})
    finally:
        purge_upload(scan_id)
        db.close()
