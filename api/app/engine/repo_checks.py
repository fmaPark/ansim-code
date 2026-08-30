"""저장소 단위 검사 — 파일 조합·부재(absence)로 판정하는 룰들이 모인다.

- SCA-01 미선언 의존성 (Task 11): 코드 import − 매니페스트 선언.
- P5·P7·P8·P9·P10 (Task 15): semgrep 단일 패턴으로 표현하기 어려운 판정.
  P5·P10은 LLM 경유 룰(G3) → review_needed 생성, P7·P8·P9 → confirmed.
"""
import re
from pathlib import Path

from app.config import SKIP_DIRS
from app.engine.deps_types import Dependency
from app.engine.findings import FindingDraft

# import 이름 ≠ 배포 패키지 이름인 대표 사례. 목록에 없는 이름은 정규화 후 그대로 비교한다.
PY_IMPORT_TO_DIST = {
    "PIL": "pillow", "yaml": "pyyaml", "bs4": "beautifulsoup4", "cv2": "opencv-python",
    "sklearn": "scikit-learn", "dateutil": "python-dateutil", "dotenv": "python-dotenv",
    "jwt": "pyjwt", "attr": "attrs", "OpenSSL": "pyopenssl", "serial": "pyserial",
    "Crypto": "pycryptodome", "MySQLdb": "mysqlclient", "psycopg2": "psycopg2-binary",
    "google": "google-api-python-client", "jose": "python-jose", "magic": "python-magic",
    "pkg_resources": "setuptools", "setuptools": "setuptools", "docx": "python-docx",
    "fitz": "pymupdf", "zoneinfo": "backports.zoneinfo",
}


def canon(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).strip().lower()


def undeclared_dependencies(deps: list[Dependency], imports_py: set[str],
                            imports_js: set[str]) -> list[tuple[str, str]]:
    """코드 import − 매니페스트 선언 = 갭 (SCA-01). → [(모듈명, 생태계)]"""
    declared_py = {canon(d.name) for d in deps if d.ecosystem == "pypi"}
    declared_js = {canon(d.name) for d in deps if d.ecosystem == "npm"}

    gaps: list[tuple[str, str]] = []
    for module in sorted(imports_py):
        candidates = {canon(module), canon(PY_IMPORT_TO_DIST.get(module, module))}
        if not candidates & declared_py:
            gaps.append((module, "pypi"))
    for module in sorted(imports_js):
        if canon(module) not in declared_js:
            gaps.append((module, "npm"))
    return gaps


# ── P5·P7~P10 저장소 단위 검사 (Task 15) ──────────────────────────────────────

CODE_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx"}
# P9 부재 판정 전용 — 처리방침은 문서다. 코드 파일(privacy.yaml·test_privacy_rules.py)이
# 파일명만으로 "처리방침 있음"을 만들어 룰을 통째로 끄던 문제를 막는다(이슈 #34).
DOC_EXTS = {".md", ".html", ".htm", ".txt", ".pdf", ".rst"}

_ROUTE = re.compile(r"@(app|api|bp)\.route\(|@router\.(get|post|put|delete)|"
                    r"\b(app|router)\.(get|post|put|delete)\(")
_SENSITIVE_PATH = re.compile(r"(?i)['\"]/?(admin|user|mypage)")
_AUTH = re.compile(r"login_required|Depends\(|authenticate|passport|jwt_required|"
                   r"@auth|check_auth|requires_auth")
_PII_KEYWORD = re.compile(r"(?i)\b(rrn|jumin|resident_?no|ssn)\b|주민등록번호|주민번호")
_LOGGING = re.compile(r"import logging|require\(['\"]winston['\"]\)|require\(['\"]pino['\"]\)|"
                      r"from ['\"]winston['\"]|from ['\"]pino['\"]")
_SCRAPER = re.compile(r"BeautifulSoup|from bs4|require\(['\"]cheerio['\"]\)|"
                      r"require\(['\"]puppeteer['\"]\)|from ['\"]puppeteer['\"]")
_HTTP_GET = re.compile(r"requests\.get|urllib|fetch\(|axios\.")
_PII_FIELD = re.compile(r"(?i)phone|birth|email|address|jumin|rrn|이름|전화|주소")
_MODEL_CLASS = re.compile(r"class \w+\((db\.Model|models\.Model|Base)\)")
_DELETION = re.compile(r"(?i)\b(delete|destroy|expire|retention|purge)\b|파기")
_PRIVACY_FILE = re.compile(r"(?i)privacy|개인정보처리방침")
_PRIVACY_ROUTE = re.compile(r"(?i)['\"]/?privacy")


def _code_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in CODE_EXTS:
            continue
        if set(p.relative_to(root).parts[:-1]) & SKIP_DIRS:
            continue
        yield p


def _read(p: Path) -> str:
    try:
        return p.read_text(errors="ignore")
    except OSError:
        return ""


def run_repo_checks(root: Path, deps=None) -> list[FindingDraft]:
    drafts: list[FindingDraft] = []
    texts = {p: _read(p) for p in _code_files(root)}
    rel = {p: str(p.relative_to(root)) for p in texts}

    # P7 — 접근통제 부재 (0414 §7.3.4, confirmed·medium)
    for p, t in texts.items():
        if _ROUTE.search(t) and _SENSITIVE_PATH.search(t) and not _AUTH.search(t):
            drafts.append(FindingDraft("P7", "medium", rel[p], None,
                                       "admin/user 라우트에 인증 장식자·미들웨어 부재", "confirmed"))

    # P8 — 접속기록 관리 부재 (0414 §7.3.4, confirmed·low)
    pii_files = [p for p, t in texts.items() if _PII_KEYWORD.search(t)]
    if pii_files and not any(_LOGGING.search(t) for t in texts.values()):
        drafts.append(FindingDraft("P8", "low", None, None,
                                   f"개인정보 취급 코드 존재({len(pii_files)}개 파일) & 로깅 설정 전무",
                                   "confirmed"))

    # P9 — 처리방침 미공개 (0414 §7.3.1, confirmed·medium — 저장소 전체 판정)
    has_policy_file = any(
        p.suffix.lower() in DOC_EXTS and _PRIVACY_FILE.search(p.name) for p in root.rglob("*")
        if p.is_file() and not (set(p.relative_to(root).parts[:-1]) & SKIP_DIRS))
    has_policy_route = any(_PRIVACY_ROUTE.search(t) for t in texts.values())
    if not has_policy_file and not has_policy_route:
        drafts.append(FindingDraft("P9", "medium", None, None,
                                   "개인정보 처리방침 파일·라우트를 찾지 못함(저장소 전체)", "confirmed"))

    # P5 — 공개 개인정보 무동의 수집 의심 (0414 §7.3.2, LLM 경유 → review_needed·medium)
    for p, t in texts.items():
        if _SCRAPER.search(t) and _HTTP_GET.search(t) and _PII_FIELD.search(t):
            drafts.append(FindingDraft("P5", "medium", rel[p], None,
                                       "크롤링 라이브러리 + 개인정보 필드 파싱 조합", "review_needed"))

    # P10 — 파기 로직 부재 의심 (0414 §7.3.5, LLM 경유 → review_needed·medium)
    model_files = [p for p, t in texts.items() if _MODEL_CLASS.search(t)]
    if model_files and not any(_DELETION.search(t) for t in texts.values()):
        drafts.append(FindingDraft("P10", "medium", rel[model_files[0]], None,
                                   "DB 모델 존재 & delete/retention/expire 로직 부재", "review_needed"))

    return drafts
