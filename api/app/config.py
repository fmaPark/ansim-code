import re

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://ansim:ansim@db:5432/ansim"
    anthropic_api_key: str = ""
    judge_model: str = "claude-sonnet-5"        # TDD §4.2
    convert_model: str = "claude-haiku-4-5"     # TDD §4.2
    judge_concurrency: int = 12                 # TDD §11 항목 1 초안
    convert_batch_size: int = 30                # TDD §11 항목 1 초안
    max_zip_bytes: int = 50 * 1024 * 1024       # TDD §3
    max_extracted_bytes: int = 500 * 1024 * 1024  # 가정(G6)
    max_extracted_files: int = 20_000           # 가정(G6)
    scan_timeout_seconds: int = 600             # 가정(G12)
    git_clone_timeout: int = 120
    # zip 업로드 원본의 임시 보관처. 격리 워크스페이스 밖이므로 파이프라인이
    # 최외곽 finally에서 직접 지운다 (G1 — workspace의 cleanup이 닿지 않는다).
    upload_dir: str = "/tmp/ansim-uploads"
    llm_cache_dir: str = "/srv/data/llm_cache"
    kisa_csv_path: str = "/srv/data/kisa/krcert_notices.csv"
    rules_dir: str = "/srv/rules"


settings = Settings()
SKIP_DIRS = {"node_modules", "venv", ".venv", ".git", "__pycache__", "__MACOSX", "dist", "build"}
OS_JUNK_FILES = {".DS_Store", "Thumbs.db"}

# 테스트 경로 판정 — 시크릿 룰을 테스트하려면 형식이 유효한 합성 시크릿이 필요하고,
# 그 필요 자체가 오탐의 원인이 된다(이슈 #29). 제외가 아니라 강등의 기준이므로
# 판정은 여기 한 곳에만 두고 엔진 전체가 공유한다.
_TEST_PATH = re.compile(
    r"(^|/)tests?/"                                  # tests/ · test/ 디렉토리
    r"|(^|/)test_[^/]+\.(py|js|jsx|ts|tsx)$"         # test_foo.py
    r"|(^|/)[^/]+_test\.(py|js|jsx|ts|tsx)$"         # foo_test.py
    r"|(^|/)[^/]+\.(test|spec)\.(js|jsx|ts|tsx)$")   # foo.test.ts · foo.spec.tsx


def is_test_path(path: str | None) -> bool:
    return bool(_TEST_PATH.search((path or "").replace("\\", "/")))
