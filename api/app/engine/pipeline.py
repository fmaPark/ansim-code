import asyncio
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.db import SessionLocal
from app.engine import fingerprint as fp
from app.engine import ingest as ing
from app.engine.catalog import rule_catalog_version
from app.engine.cvss import NULL_REASON_NO_VECTOR, derive_cvss3
from app.engine.deps_npm import npm_parse_markers, parse_npm_deps
from app.engine.deps_python import parse_python_deps, python_parse_markers
from app.engine.osv import OsvResult, osv_snapshot_date, query_osv
from app.engine.sbom import build_sbom, classify_supply_chain, vendored_dependencies
from app.engine.workspace import scan_workspace
from app.models import SbomComponent, Scan

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


def stage_sbom(db, scan, root: Path) -> dict:
    """§11.2 현황 진단 — 의존성 파싱 → 15속성 SBOM → 공급망 분류 (Task 6·7·8).

    깨진 매니페스트·setup.py 전용 저장소는 예외로 죽이지 않고 마커로 남긴다.
    """
    deps = parse_python_deps(root) + parse_npm_deps(root)
    deps += vendored_dependencies(root, deps)
    markers = python_parse_markers(root) + npm_parse_markers(root)
    rows = build_sbom(deps, root)

    components = [SbomComponent(scan_id=scan.id, **row) for row in rows]
    db.add_all(components)
    report = dict(scan.report_json or {})
    report["parse_markers"] = [{"kind": m.kind, "detail": m.detail} for m in markers]
    _set(db, scan,
         supply_chain_class=classify_supply_chain(deps, root),
         report_json=report)
    log.info("SBOM 생성", extra={"scan_id": str(scan.id), "component_count": len(rows),
                                 "supply_chain_class": scan.supply_chain_class,
                                 "parse_marker_count": len(markers)})
    return {"deps": deps, "components": components, "markers": markers}


def _apply_vulns(component: SbomComponent, infos) -> None:
    """OSV 결과를 SBOM ⑩⑬⑭⑮에 채운다 — CVSS는 가장 높은 Base를 대표값으로 쓴다."""
    component.vulnerability_db = [{"id": v.id, "source": v.source} for v in infos]
    component.cve_ids = sorted({cve for v in infos for cve in v.cve_ids})

    scored = [(derive_cvss3(v.cvss_vector), v) for v in infos]
    scored = [(d, v) for d, v in scored if d]
    if scored:
        (base, impact, expl, severity), _worst = max(scored, key=lambda t: t[0][0])
        component.cvss_base, component.cvss_impact = base, impact
        component.cvss_exploitability, component.cvss_severity = expl, severity
        component.cvss_null_reason = None
    else:
        component.cvss_null_reason = NULL_REASON_NO_VECTOR
        # 벡터가 없어도 OSV가 준 등급 문자열은 살린다(등급 산정은 confirmed 사실만 쓴다 — G3).
        ranked = [v.severity for v in infos if v.severity != "unknown"]
        component.cvss_severity = ranked[0] if ranked else None


async def stage_osv(db, scan, components: list[SbomComponent]) -> OsvResult:
    """§11.3 위험 분석 1단계 — purl 배치 질의 → SBOM ⑩⑬⑭⑮ (Task 9)."""
    result = await query_osv([c.unique_id for c in components])
    for component in components:
        infos = result.vulns.get(component.unique_id)
        if infos:
            _apply_vulns(component, infos)
    report = dict(scan.report_json or {})
    report["osv_incomplete"] = result.incomplete       # 리포트의 "일부 미대조" 표시 입력
    _set(db, scan, vuln_db_snapshot_date=osv_snapshot_date(), report_json=report)
    log.info("OSV 대조", extra={"scan_id": str(scan.id), "queried": len(components),
                                "vulnerable": len(result.vulns), "incomplete": result.incomplete})
    return result


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
                    ctx = await asyncio.to_thread(stage_sbom, db, scan, res.root)
                    _set(db, scan, current_stage="위험분석")   # §11.3 — Task 9~17
                    await stage_osv(db, scan, ctx["components"])
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
