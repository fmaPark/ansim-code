import uuid

from pydantic import BaseModel


class ScanAccepted(BaseModel):
    scan_id: uuid.UUID


class ScanStatus(BaseModel):
    status: str
    current_stage: str | None
    grade: str | None
    error_message: str | None
    previous_comparison: dict | None = None   # 재진단 비교는 Task 21이 채운다
