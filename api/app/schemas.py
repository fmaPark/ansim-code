import uuid

from pydantic import BaseModel


class ScanAccepted(BaseModel):
    scan_id: uuid.UUID


class ScanStatus(BaseModel):
    status: str
    source_type: str                          # git|zip — FE PublishFlow가 공개 가능 여부를 분기한다
    current_stage: str | None
    grade: str | None
    error_message: str | None
    previous_comparison: dict | None = None   # 재진단 비교는 Task 21이 채운다
