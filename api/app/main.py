import json
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import SessionLocal, engine
from app.engine.catalog import load_rules, rule_catalog_version
from app.engine.pipeline import purge_orphan_uploads
from app.models import Base, Rule
from app.routes import scans

# LogRecord가 항상 채우는 속성 — 이 이름들만 빼면 나머지는 호출부가 extra=로 실은 값이다.
_RESERVED = frozenset(
    logging.LogRecord(name="", level=0, pathname="", lineno=0, msg="", args=None, exc_info=None).__dict__
) | {"message", "asctime", "taskName"}


class JsonFormatter(logging.Formatter):
    """TDD §10 구조화 JSON 로그 — 스캔 단계·소요 시간·외부 API 상태를 extra= 필드로 싣는다."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record),
            "lvl": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        payload.update({k: v for k, v in record.__dict__.items() if k not in _RESERVED})
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_json_logging():
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[h], force=True)


def seed_rules():
    """rules/catalog.yaml → Rule 테이블 upsert. verdict·detection은 YAML 전용이라 제외된다."""
    columns = set(Rule.__table__.columns.keys())
    rows = load_rules()
    with SessionLocal() as db:
        for row in rows:
            db.merge(Rule(**{k: v for k, v in row.items() if k in columns}))
        db.commit()
    logging.info(
        "룰 카탈로그 시드 완료",
        extra={"rule_count": len(rows), "rule_catalog_version": rule_catalog_version()},
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 마이그레이션 도구는 쓰지 않는다(가정: 데모 규모 — 스키마 변경 시 docker compose down -v).
    Base.metadata.create_all(engine)
    seed_rules()
    purge_orphan_uploads()   # G1: 이전 프로세스가 남긴 업로드 원본이 있으면 지운다
    yield


setup_json_logging()
app = FastAPI(title="AnsimCode API", lifespan=lifespan)
app.include_router(scans.router)


@app.get("/health")
def health():
    return {"status": "ok"}
