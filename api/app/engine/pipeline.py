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
from app.engine.cvss import NULL_REASON_NO_VECTOR, derive_cvss3
from app.engine.deps_npm import npm_parse_markers, parse_npm_deps
from app.engine.deps_python import parse_python_deps, python_parse_markers
from app.engine.grade import GradeResult, calc_grade, cve_rows_from_osv
from app.engine.kisa import kisa_snapshot_label, load_kisa
from app.engine.osv import OsvResult, osv_snapshot_date, query_osv
from app.engine.imports_py import extract_python_imports
from app.engine.sbom import build_sbom, classify_supply_chain, component_row, vendored_dependencies
from app.engine.sca_rules import component_label, evaluate_sca_rules, matrix_0322
from app.engine.semgrep_runner import extract_js_imports
from app.engine.workspace import scan_workspace
from app.models import Finding, SbomComponent, Scan

log = logging.getLogger(__name__)

_EVIDENCE_CVE_LIMIT = 3      # SCA-03 제품명 교차 evidence의 CVE 나열 상한(Django는 26건까지 나온다)


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
    component.vulnerability_db = [
        {"id": v.id, "source": v.source, "fixed": v.fixed_version} for v in infos]   # SCA-04 입력
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


def stage_kisa(db, scan, components: list[SbomComponent]) -> list[Finding]:
    """§11.3 위험 분석 2단계 — KISA 공지 교차 → SCA-03 (Task 10).

    교차는 두 경로다(배포본에 공지 본문이 없어서다 — `data/kisa/PROVENANCE.md`).
      1. **CVE 교차** — OSV CVE ∩ 공지 제목 CVE. 취약점별 출처(⑩)에도 KISA를 남긴다.
      2. **제품명 교차** — 보안공지 제목의 제품명 ↔ 컴포넌트명. **OSV가 이미 취약하다고
         판정한 컴포넌트에만** 적용한다(오탐 차단). KISA가 그 CVE를 발령한 건
         아니므로 `vulnerability_db`에는 넣지 않는다 — 출처 오귀속 방지.

    등급은 **단계가 바뀌지 않는다** — 대상 컴포넌트는 정의상 SCA-02가 이미 confirmed로
    잡은 것들이라 `_grade_of`의 판정이 달라질 입력이 없다. 다만 confirmed 발견이 늘어난
    만큼 `grade.py`의 `_blocking`이 세는 **상향 조건 건수(`upgrade_count`)와 blocking
    목록은 증가**한다("이 N건 해결 시 상승"의 N).

    OSV가 `incomplete`여도 얻은 CVE에 대한 교차는 그대로 수행한다(부분 결과 정책).
    """
    snapshot = load_kisa()
    findings: list[Finding] = []
    product_matches = 0
    if snapshot:
        for component in components:
            label = component_label(component.component_name, component.version)
            matched = [cve for cve in (component.cve_ids or []) if cve in snapshot]
            if matched:
                sources = list(component.vulnerability_db or [])
                for cve in matched:
                    notice = snapshot.by_cve[cve]
                    sources.append({"id": cve, "source": "KISA", "notice_url": notice.url,
                                    "match": "cve"})
                    findings.append(Finding(
                        scan_id=scan.id, rule_id="SCA-03", severity="high",
                        file_path=None, line=None,
                        evidence=(f"{label} — {cve}: 국내 보안공지 발령(CVE 교차) "
                                  f"「{notice.title}」 {notice.url}"),
                        status="confirmed"))
                component.vulnerability_db = sources    # ⑩ 취약점별 출처에 KISA 추가
                continue

            if not component.cve_ids:                   # OSV 미취약 컴포넌트는 대상 아님
                continue
            notice = snapshot.match_product(component.component_name)
            if notice is None:
                continue
            product_matches += 1
            cves = list(component.cve_ids)
            shown = ", ".join(cves[:_EVIDENCE_CVE_LIMIT])
            if len(cves) > _EVIDENCE_CVE_LIMIT:
                shown += f" 외 {len(cves) - _EVIDENCE_CVE_LIMIT}건"
            findings.append(Finding(
                scan_id=scan.id, rule_id="SCA-03", severity="high",
                file_path=None, line=None,
                evidence=(f"{label} — {shown}: 국내 보안공지 발령"
                          f"(제품명 일치) 「{notice.title}」({notice.date} 보호나라 보안공지) "
                          f"{notice.url} · 공공데이터 배포본은 공지 제목만 제공하므로 "
                          f"공지 본문의 CVE 일치는 확인되지 않았습니다"),
                status="confirmed"))
        db.add_all(findings)

    _set(db, scan, vuln_db_snapshot_date=f"{osv_snapshot_date()}; {kisa_snapshot_label()}")
    log.info("KISA 교차", extra={"scan_id": str(scan.id), "kisa_cve_count": len(snapshot),
                                 "kisa_advisory_count": len(snapshot.advisories),
                                 "sca03_findings": len(findings),
                                 "sca03_product_matches": product_matches})
    return findings


def stage_sca_rules(db, scan, root: Path, deps, components: list[SbomComponent]) -> list[Finding]:
    """§11.3 위험 분석 3단계 — SCA 룰 12종 + 0322 표 5-1 매트릭스 (Task 11).

    SCA-03은 KISA 교차 단계가 이미 만들었으므로 여기서 다시 만들지 않는다.
    """
    rows = [component_row(c) for c in components]
    drafts = evaluate_sca_rules(deps, rows, extract_python_imports(root),
                                extract_js_imports(root), root)
    findings = [Finding(scan_id=scan.id, rule_id=d.rule_id, severity=d.severity,
                        file_path=d.file_path, line=d.line, evidence=d.evidence,
                        status=d.status) for d in drafts]
    db.add_all(findings)

    report = dict(scan.report_json or {})
    report["matrix_0322"] = matrix_0322(scan.supply_chain_class, rows)
    _set(db, scan, report_json=report)
    log.info("SCA 룰 finding 저장", extra={"scan_id": str(scan.id), "finding_count": len(findings)})
    return findings


def stage_grade(db, scan, cve_rows: list[dict]) -> GradeResult:
    """§11.3 위험 분석 말미 — 등급 결정론(P0-3, Task 17).

    입력은 DB에 확정된 Finding 행(status·rule_id·severity)과 CVE 심각도뿐이다.
    LLM 산출물은 calc_grade의 인자에 존재하지 않으므로 등급에 닿을 수 없다(G3).
    """
    findings = db.query(Finding).filter(Finding.scan_id == scan.id).order_by(Finding.id).all()
    result = calc_grade(findings, cve_rows)

    blocking = set(result.blocking_finding_ids)
    for f in findings:
        f.grade_blocking = f.id in blocking
    _set(db, scan, grade=result.grade)

    log.info("등급 산정", extra={"scan_id": str(scan.id), "grade": result.grade,
                                 "blocking_findings": len(result.blocking_finding_ids),
                                 "blocking_cves": len(result.blocking_cve_ids),
                                 "upgrade_target": result.upgrade_target,
                                 "upgrade_count": result.upgrade_count})
    return result


async def stage_report(db, scan, registry, grade_result=None) -> None:
    """§11.4 대책 수립 — 변환(Task 18) + 이중 리포트 조립(Task 19).

    원본 코드가 아니라 DB에 확정된 Finding 행만 쓰므로 워크스페이스 파기 이후에 돈다(G1).
    """
    from app.llm.convert import generate_texts   # 순환 import 회피(convert가 analysis를 쓴다)
    from app.report.builder import build_reports

    findings = db.query(Finding).filter(Finding.scan_id == scan.id).order_by(Finding.id).all()
    await generate_texts(scan, findings, registry=registry)
    db.commit()

    components = (db.query(SbomComponent).filter(SbomComponent.scan_id == scan.id)
                  .order_by(SbomComponent.id).all())
    scratch = dict(scan.report_json or {})        # parse_markers·osv_incomplete·matrix_0322
    dev, easy = build_reports(scan, findings, [component_row(c) for c in components],
                              scratch.get("matrix_0322"), scratch.get("osv_incomplete", False),
                              grade_result=grade_result)
    # 기존 스크래치 키를 보존한 채 병합한다 — /sbom이 parse_markers를 읽는다.
    _set(db, scan, report_json={**scratch, **dev}, easy_report_json=easy)
    log.info("대책 수립", extra={"scan_id": str(scan.id), "finding_count": len(findings)})


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
                    # M3: SBOM 취약점 대조 + SCA 룰 — Task 9~11
                    osv_result = await stage_osv(db, scan, ctx["components"])
                    await asyncio.to_thread(stage_kisa, db, scan, ctx["components"])
                    await asyncio.to_thread(stage_sca_rules, db, scan, res.root,
                                            ctx["deps"], ctx["components"])
                    # M4: 정적 룰(gitleaks·semgrep·repo_checks) + 마스킹(P0-2) — Task 12~15
                    drafts, registry = await asyncio.to_thread(analysis.run_static_stage, res.root)
                    # M4: LLM judge — P1·P4 합성 + 스니펫(파기 전) + 12 병렬, status 불변(G3)
                    await analysis.run_llm_stage(scan, drafts, res.root, registry)
                    analysis.persist_findings(db, scan.id, drafts)
                    # 등급 결정론 — static confirmed + CVE만 (Task 17, P0-3)
                    grade_result = stage_grade(db, scan, cve_rows_from_osv(osv_result))
                _set(db, scan, current_stage="대책수립")   # §11.4 — Task 18~19
                await stage_report(db, scan, registry, grade_result)
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
