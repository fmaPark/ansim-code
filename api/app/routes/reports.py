import uuid

from fastapi import APIRouter, HTTPException

from app.db import SessionLocal
from app.models import Scan, SbomComponent

router = APIRouter(prefix="/api/scans", tags=["reports"])

# 0309 §5.2 15속성 — 이 순서 그대로 내려보낸다(프론트가 JSON을 그대로 저장한다).
SBOM_KEYS = (
    "validation_tool", "supplier", "author", "component_name", "version", "unique_id",
    "component_hash", "license_name", "license_usage", "vulnerability_db", "relationship",
    "release_date", "cve_ids", "cvss_base", "cvss_severity",
)
# 15속성 밖의 보조 필드 — §6.14 3값 중 나머지와 null 사유, 내부 생태계 구분.
SBOM_EXTRA_KEYS = ("cvss_impact", "cvss_exploitability", "cvss_null_reason", "ecosystem")


def serialize_component(c: SbomComponent) -> dict:
    return {k: getattr(c, k) for k in SBOM_KEYS + SBOM_EXTRA_KEYS}


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
            "components": [serialize_component(c) for c in rows],
            "supply_chain_class": scan.supply_chain_class,
            "parse_markers": markers,          # 파싱 불가 선언 파일 (G7·깨진 매니페스트)
            "generated_by": "AnsimCode",
        }
