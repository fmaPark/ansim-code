import uuid

from fastapi import APIRouter, HTTPException

from app.db import SessionLocal
from app.engine.sbom import component_row
from app.models import Scan, SbomComponent

router = APIRouter(prefix="/api/scans", tags=["reports"])


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
