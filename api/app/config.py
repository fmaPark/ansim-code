from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://ansim:ansim@db:5432/ansim"
    gemini_api_key: str = ""
    # TDD §4.2(v0.6)의 가정은 2.5-flash / 2.5-flash-lite였으나 실키 확인 결과 두 모델 모두
    # "no longer available to new users"(404)다. thinking_budget=0을 그대로 받는 3.x 조합으로
    # 대체했다(2026-08-30 실측 — docs/measurements.md M8, 기획 사후 승인 대상 §11 항목 9 ①).
    judge_model: str = "gemini-3.5-flash"          # TDD §4.2 (모델 가정 정정)
    convert_model: str = "gemini-3.1-flash-lite"   # TDD §4.2 (모델 가정 정정)
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
