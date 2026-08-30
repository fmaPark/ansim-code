import re

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
    # 스캔당 judge 호출 상한 (TDD §6·§11 항목 1이 예고한 장치 — 2026-08-30 기획 D2ⓑ 채택).
    # Gemini 무료 티어가 모델당 5 RPM이라 12 병렬은 6번째 요청부터 429다. 상한을 넘는
    # 후보는 설명 없이 review_needed로 남는다 — 등급은 static 경로라 영향 없다(G3).
    # 값 3은 실측 결과다: 상한 5는 버스트가 쿼터와 정확히 같아 여유가 없어 429 2건이
    # 남았다. 3이면 데모의 스캔→재진단 연속(같은 분에 2 버스트)과 JSON 파싱 재요청까지
    # 흡수한다. 0이면 무제한 — 유료 티어 전환 시 이 값만 올리면 된다(D2ⓒ).
    judge_max_calls: int = 3
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
