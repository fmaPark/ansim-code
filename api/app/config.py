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
