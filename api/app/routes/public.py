"""등급 공개 — git 전용 opt-in 2단계(.ansimcode 소유 증명) + 공개 페이지 + SVG 배지.

G10(TDD §4.5, ADR v1.3): 공개는 git 스캔만, zip은 소유 증명이 불가능해 403.
공개 데이터에는 G11 재현성 앵커 4종과 "인증 아님" 고지를 항상 싣는다.
"""
import asyncio
import hashlib
import secrets
import uuid

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from app.db import SessionLocal
from app.engine import ingest as ing
from app.engine.grade import CAUTION, DANGER, SAFE
from app.engine.workspace import scan_workspace
from app.models import Scan

router = APIRouter(tags=["public"])

LEGAL_NOTICE = ("본 등급은 인증이 아닌 자가점검 보조 결과입니다. "
                "진단 시점의 코드(콘텐츠 지문 기준)에 대한 자동 분석이며 법적 효력이 없습니다.")  # §11 항목 7 placeholder
ZIP_PUBLISH_NOTICE = ("zip 업로드 진단은 소유 증명이 불가능해 등급 공개를 지원하지 않습니다. "
                      "공개가 필요하면 공개 git 저장소 URL로 다시 진단해 주세요.")               # §11 항목 8 placeholder

GRADE_COLORS = {SAFE: "#2b8a3e", CAUTION: "#f08c00", DANGER: "#c2255c"}

BADGE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="140" height="20" role="img">
<rect width="70" height="20" fill="#555"/><rect x="70" width="70" height="20" fill="{color}"/>
<g fill="#fff" font-family="sans-serif" font-size="11" text-anchor="middle">
<text x="35" y="14">안심코드</text><text x="105" y="14">{grade} {date}</text></g></svg>"""

BASE_URL = "http://localhost:8080"   # 로컬 데모 진입점 (ADR §5 — 클라우드 배포 없음)


class PublishBody(BaseModel):
    confirm: bool = False


async def _read_publish_body(request: Request) -> PublishBody:
    # 1단계는 body 없이 호출된다 — 빈 본문을 422로 튕기지 않기 위해 직접 파싱한다.
    raw = await request.body()
    if not raw:
        return PublishBody()
    return PublishBody.model_validate_json(raw)


def _clone_ansimcode_token(source_ref: str) -> str | None:
    """저장소를 얕게 clone해 루트 .ansimcode 내용을 읽고 워크스페이스는 즉시 파기한다(G1)."""
    with scan_workspace() as ws:
        result = ing.ingest_git(source_ref, ws)
        marker = result.root / ".ansimcode"
        if not marker.is_file():
            return None
        return marker.read_text().strip()


@router.post("/api/scans/{scan_id}/publish")
async def publish(scan_id: uuid.UUID, request: Request):
    body = await _read_publish_body(request)
    with SessionLocal() as db:
        scan = db.get(Scan, scan_id)
        if scan is None:
            raise HTTPException(404, "존재하지 않는 스캔입니다")
        if scan.source_type != "git":
            raise HTTPException(403, ZIP_PUBLISH_NOTICE)
        if scan.status != "done":
            raise HTTPException(409, f"완료된 진단만 공개할 수 있습니다 (status={scan.status})")

        if not body.confirm:                       # 1단계 — 일회용 토큰 발급
            token = secrets.token_urlsafe(16)
            scan.publish_token = token
            db.commit()
            return {"token": token,
                    "instructions": ("저장소 루트에 .ansimcode 파일을 만들어 "
                                     "이 토큰 한 줄을 커밋한 뒤 다시 확인을 누르세요")}

        # 2단계 — .ansimcode 소유 증명
        if not scan.publish_token:
            raise HTTPException(409, "발급된 토큰이 없습니다. 공개하기를 먼저 눌러 토큰을 발급받으세요")
        source_ref, expected = scan.source_ref, scan.publish_token

    try:
        committed = await asyncio.to_thread(_clone_ansimcode_token, source_ref)
    except ing.ValidationError as e:
        raise HTTPException(409, f"저장소 확인 실패: {e}")
    if committed != expected:
        raise HTTPException(409, ".ansimcode 토큰이 일치하지 않습니다. "
                                 "발급된 토큰을 저장소 루트 .ansimcode로 커밋했는지 확인해 주세요")

    with SessionLocal() as db:
        scan = db.get(Scan, scan_id)
        if scan.public_slug is None:
            scan.public_slug = secrets.token_urlsafe(8)
        scan.is_public = True
        db.commit()
        slug = scan.public_slug
    return {
        "public_url": f"/g/{slug}",
        "badge_markdown": (f"[![안심코드]({BASE_URL}/api/public/badge/{slug}.svg)]"
                           f"({BASE_URL}/g/{slug})"),
    }


def _public_scan(db, slug: str) -> Scan:
    scan = db.query(Scan).filter(Scan.public_slug == slug, Scan.is_public.is_(True)).first()
    if scan is None:
        raise HTTPException(404, "공개된 등급이 없습니다")
    return scan


@router.get("/api/public/grades/{slug}")
def public_grade(slug: str):
    with SessionLocal() as db:
        scan = _public_scan(db, slug)
        return {
            "grade": scan.grade,
            "easy_report": scan.easy_report_json,
            "provenance": {                       # G11 재현성 앵커 4종
                "content_fingerprint": scan.content_fingerprint,
                "fingerprint_type": scan.fingerprint_type,
                "rule_catalog_version": scan.rule_catalog_version,
                "llm_model_id": scan.llm_model_id,
                "vuln_db_snapshot_date": scan.vuln_db_snapshot_date,
            },
            "scanned_at": scan.created_at.isoformat(),
            "disclaimer": LEGAL_NOTICE,
        }


@router.get("/api/public/badge/{slug}.svg")
def public_badge(slug: str, request: Request):
    with SessionLocal() as db:
        scan = _public_scan(db, slug)
        grade, scanned_at = scan.grade, scan.created_at.isoformat()

    etag = 'W/"{}"'.format(
        hashlib.sha256(f"{slug}{grade}{scanned_at}".encode()).hexdigest()[:16])
    headers = {"Cache-Control": "max-age=300, must-revalidate", "ETag": etag}
    if request.headers.get("if-none-match") == etag:   # GitHub camo 캐싱 대응 (TDD §4.4)
        return Response(status_code=304, headers=headers)
    svg = BADGE_SVG.format(color=GRADE_COLORS.get(grade, "#555"),
                           grade=grade, date=scanned_at[:10])
    return Response(content=svg, media_type="image/svg+xml", headers=headers)
