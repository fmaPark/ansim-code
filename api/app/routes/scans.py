import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.db import SessionLocal
from app.engine.diff import compare_scans
from app.engine.pipeline import run_scan, upload_path
from app.models import Finding, Scan
from app.schemas import ScanAccepted, ScanStatus

router = APIRouter(prefix="/api/scans", tags=["scans"])

_CHUNK = 1024 * 1024


async def _save_upload(upload, scan_id) -> None:
    dest = upload_path(scan_id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:                # 50MB를 통째로 메모리에 올리지 않는다
        while chunk := await upload.read(_CHUNK):
            f.write(chunk)


async def _multipart_upload(request: Request):
    form = await request.form()
    upload = form.get("file")
    if upload is None or not hasattr(upload, "filename"):
        raise HTTPException(422, "zip 파일을 file 필드로 보내주세요")
    return upload


@router.post("", status_code=202, response_model=ScanAccepted)
async def create_scan(request: Request, background_tasks: BackgroundTasks):
    """git URL(JSON)과 zip(multipart)을 한 경로에서 받는다.

    본문 형식이 둘로 갈려 FastAPI의 자동 바디 파싱으로는 한쪽이 다른 쪽의 바디를
    소비해버리므로 content-type으로 직접 분기한다.
    """
    ctype = request.headers.get("content-type", "")
    upload = None
    if ctype.startswith("application/json"):
        payload = await request.json()
        git_url = (payload or {}).get("git_url")
        if not git_url:
            raise HTTPException(422, "git_url이 필요합니다")
        scan = Scan(source_type="git", source_ref=git_url)
    elif ctype.startswith("multipart/form-data"):
        upload = await _multipart_upload(request)
        scan = Scan(source_type="zip", source_ref=upload.filename or "upload.zip")
    else:
        raise HTTPException(415, "application/json 또는 multipart/form-data만 지원합니다")

    with SessionLocal() as db:
        db.add(scan)
        db.commit()
        scan_id = scan.id

    if upload is not None:
        await _save_upload(upload, scan_id)

    background_tasks.add_task(run_scan, scan_id)
    return ScanAccepted(scan_id=scan_id)


@router.post("/{scan_id}/rescan", status_code=202, response_model=ScanAccepted)
async def rescan(scan_id: uuid.UUID, request: Request, background_tasks: BackgroundTasks):
    """재진단 — git은 동일 URL 재clone, zip은 수정본 재업로드 (TDD §4.4·§4.7).

    새 Scan을 만들고 `previous_scan_id`로 이력을 잇는다(0259 §11.5 이력관리 대장).
    파이프라인은 최초 진단과 동일하다.
    """
    with SessionLocal() as db:
        origin = db.get(Scan, scan_id)
        if origin is None:
            raise HTTPException(404, "존재하지 않는 스캔입니다")
        source_type, source_ref = origin.source_type, origin.source_ref

    upload = None
    if source_type == "zip":
        # zip 원본은 진단 직후 파기된다(G1) — 재진단에는 수정본 재업로드가 필수다.
        if not request.headers.get("content-type", "").startswith("multipart/form-data"):
            raise HTTPException(422, "zip 진단의 재진단은 수정된 zip 재업로드가 필요합니다")
        upload = await _multipart_upload(request)
        source_ref = upload.filename or source_ref

    new_scan = Scan(source_type=source_type, source_ref=source_ref, previous_scan_id=scan_id)
    with SessionLocal() as db:
        db.add(new_scan)
        db.commit()
        new_id = new_scan.id

    if upload is not None:
        await _save_upload(upload, new_id)

    background_tasks.add_task(run_scan, new_id)
    return ScanAccepted(scan_id=new_id)


@router.get("/{scan_id}", response_model=ScanStatus)
def get_scan(scan_id: uuid.UUID):
    with SessionLocal() as db:
        scan = db.get(Scan, scan_id)
        if scan is None:
            raise HTTPException(404, "존재하지 않는 스캔입니다")

        comparison = None
        if scan.previous_scan_id and scan.status == "done":
            previous = db.get(Scan, scan.previous_scan_id)
            if previous is not None:
                comparison = compare_scans(
                    previous, scan,
                    _findings(db, previous.id), _findings(db, scan.id))

        return ScanStatus(
            status=scan.status,
            current_stage=scan.current_stage,
            grade=scan.grade,
            error_message=scan.error_message,
            previous_comparison=comparison,
        )


def _findings(db, scan_id):
    return db.query(Finding).filter(Finding.scan_id == scan_id).order_by(Finding.id).all()
