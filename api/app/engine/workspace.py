import logging
import tempfile
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def scan_workspace(on_purged=None):
    """P0-1: 어떤 실패 경로에서도 finally에서 디렉토리 삭제 (TDD §8)."""
    tmp = tempfile.TemporaryDirectory(prefix="ansim-scan-")
    try:
        yield Path(tmp.name)
    finally:
        try:
            tmp.cleanup()
            if on_purged:
                on_purged()          # purged_at 기록 콜백
        except Exception:
            logging.error("workspace purge failed", extra={"workspace": tmp.name})  # 삭제 실패는 에러 로그
