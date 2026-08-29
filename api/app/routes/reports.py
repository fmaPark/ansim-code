import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException

from app.db import SessionLocal
from app.engine.sbom import component_row
from app.models import Scan, SbomComponent
from app.report.checklist import CHECKLIST, CHECKLIST_DISCLAIMER

router = APIRouter(prefix="/api/scans", tags=["reports"])


@router.get("/{scan_id}/report")
def get_report(scan_id: uuid.UUID, mode: Literal["dev", "easy"] = "dev"):
    """개발자용 조항 인용 리포트 / `?mode=easy` 시민용 (TDD §4.4)."""
    with SessionLocal() as db:
        scan = db.get(Scan, scan_id)
        if scan is None:
            raise HTTPException(404, "존재하지 않는 스캔입니다")
        report = scan.easy_report_json if mode == "easy" else scan.report_json
        if scan.status != "done" or not report:
            raise HTTPException(409, f"진단이 완료되지 않았습니다 (status={scan.status})")
        return report


@router.get("/{scan_id}/checklist")
def get_checklist(scan_id: uuid.UUID):
    """조직 요구사항 통합 체크리스트 — 스캔과 무관한 정적 데이터지만 경로는 TDD §4.4 유지."""
    with SessionLocal() as db:
        if db.get(Scan, scan_id) is None:
            raise HTTPException(404, "존재하지 않는 스캔입니다")
    return {"items": CHECKLIST, "disclaimer": CHECKLIST_DISCLAIMER}


@router.get("/{scan_id}/sbom")
def get_sbom(scan_id: uuid.UUID):
    with SessionLocal() as db:
        scan = db.get(Scan, scan_id)
        if scan is None:
            raise HTTPException(404, "존재하지 않는 스캔입니다")
        rows = (
            db.query(SbomComponent)
            .filter(SbomComponent.scan_id == scan_id)
            .order_by(SbomComponent.ecosystem, SbomComponent.component_name)
            .all()
        )
        markers = (scan.report_json or {}).get("parse_markers") or []
        return {
            "components": [component_row(c) for c in rows],
            "supply_chain_class": scan.supply_chain_class,
            "parse_markers": markers,          # 파싱 불가 선언 파일 (G7·깨진 매니페스트)
            "generated_by": "AnsimCode",
        }
