import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.db import SessionLocal
from app.engine.pipeline import run_scan, upload_path
from app.models import Scan
from app.schemas import ScanAccepted, ScanStatus

router = APIRouter(prefix="/api/scans", tags=["scans"])

_CHUNK = 1024 * 1024


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
        form = await request.form()
        upload = form.get("file")
        if upload is None or not hasattr(upload, "filename"):
            raise HTTPException(422, "zip 파일을 file 필드로 보내주세요")
        scan = Scan(source_type="zip", source_ref=upload.filename or "upload.zip")
    else:
        raise HTTPException(415, "application/json 또는 multipart/form-data만 지원합니다")

    with SessionLocal() as db:
        db.add(scan)
        db.commit()
        scan_id = scan.id

    if upload is not None:
        dest = upload_path(scan_id)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:            # 50MB를 통째로 메모리에 올리지 않는다
            while chunk := await upload.read(_CHUNK):
                f.write(chunk)

    background_tasks.add_task(run_scan, scan_id)
    return ScanAccepted(scan_id=scan_id)


@router.get("/{scan_id}", response_model=ScanStatus)
def get_scan(scan_id: uuid.UUID):
    with SessionLocal() as db:
        scan = db.get(Scan, scan_id)
        if scan is None:
            raise HTTPException(404, "존재하지 않는 스캔입니다")
        return ScanStatus(
            status=scan.status,
            current_stage=scan.current_stage,
            grade=scan.grade,
            error_message=scan.error_message,
        )
