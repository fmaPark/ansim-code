import json
import logging
import sys

from fastapi import FastAPI

# logging.LogRecord가 항상 채우는 속성 — 이 이름들만 빼면 나머지는 호출부가 extra=로 실은 값이다.
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


setup_json_logging()
app = FastAPI(title="AnsimCode API")


@app.get("/health")
def health():
    return {"status": "ok"}
