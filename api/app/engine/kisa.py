"""KISA 보호나라(KrCERT) 보안공지 스냅샷 로더 + 교차 (TDD §4.6).

배포본(data.go.kr/15155789)은 게시판 **목록 메타데이터**만 담는다 — 본문·링크 컬럼이
없어서 제목에 실린 CVE만 뽑히고, 그렇게 뽑히는 192건은 전부 국내 제품 CVE다
(pypi/npm 생태계 CVE는 0건). 정작 Django·aiohttp·Node.js를 다루는 `보안공지`
2,316건은 제목에 CVE가 없다. 그래서 교차 경로를 둘로 둔다 — 상세는
`data/kisa/PROVENANCE.md`.

  1. **CVE 교차** — 제목에서 추출한 CVE ∩ OSV CVE (`by_cve`)
  2. **제품명 교차** — 보안공지 제목의 제품명 ↔ SBOM 컴포넌트명 (`match_product`)

컬럼 구성은 배포본마다 바뀔 수 있다. 헤더 행이 있으면 헤더명으로 컬럼을 매핑하고,
없으면 셀의 형태로 판별한다. `작성자` 컬럼은 KISA 담당자 실명이라 **읽지 않는다**.
"""

import csv
import io
import logging
import re
from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path

from app.config import settings

log = logging.getLogger(__name__)

CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}")
_URL_RE = re.compile(r"https?://\S+")
_DATE_RE = re.compile(r"\d{4}[-./]\d{1,2}[-./]\d{1,2}")
_NUMERIC_RE = re.compile(r"^\d+$")                    # 순번·조회수 — 제목이 아니다
_ENCODINGS = ("utf-8-sig", "cp949")      # data.go.kr 배포본이 EUC-KR(cp949)인 경우 대비

SNAPSHOT_DATE_FILENAME = "SNAPSHOT_DATE"

# 개별 공지의 상세 URL은 opaque id라 CSV에서 복원할 수 없다 — 게시판 URL로 대신한다.
NOTICE_BOARD_URL = "https://knvd.krcert.or.kr/info/vuln/notice"
ADVISORY_BOARD = "보안공지"               # 제품명 교차 대상 게시판(오탐 차단)
MIN_PRODUCT_NAME_LEN = 4                  # 3글자 이하 컴포넌트명은 제목과 우연히 겹친다
TITLE_MAX_LEN = 200

# 제품명이라기엔 너무 흔한 단어 — 공지 제목의 다른 제품에 얹혀 걸린다
# (`core` ← "Microsoft XML Core Services"). 제품명 교차에서 제외한다.
GENERIC_NAMES = frozenset({
    "base", "client", "code", "common", "core", "data", "date", "file", "files",
    "http", "init", "json", "main", "module", "name", "node", "package", "server",
    "service", "source", "test", "tests", "time", "tools", "user", "util", "utils",
})

# 헤더명 → 컬럼 역할. 부분 문자열로 맞춘다(공백 제거·소문자화 후 비교).
_TITLE_HEADERS = ("제목", "title", "subject")
_DATE_HEADERS = ("작성일", "게시일", "등록일", "date")
_URL_HEADERS = ("링크", "url", "주소")
_BOARD_HEADERS = ("게시판종류", "구분", "board")
_PERSON_HEADERS = ("작성자", "담당자", "writer", "author")     # 개인정보 — 로드 제외


@dataclass(frozen=True)
class KisaNotice:
    title: str
    url: str
    date: str
    board: str = ""


@dataclass(frozen=True)
class _Columns:
    """헤더로 확인된 컬럼 위치. 전부 None이면 형태 휴리스틱으로 판별한다."""
    title: int | None = None
    date: int | None = None
    url: int | None = None
    board: int | None = None
    skip: frozenset = frozenset()         # 작성자 등 읽지 않는 컬럼


@dataclass
class KisaSnapshot:
    """스냅샷 1개 = CVE 색인 + 보안공지 제목 색인."""

    by_cve: dict[str, KisaNotice] = field(default_factory=dict)
    advisories: list[KisaNotice] = field(default_factory=list)
    _titles: list[tuple[str, KisaNotice]] = field(default_factory=list, repr=False)

    def __bool__(self) -> bool:
        return bool(self.by_cve or self.advisories)

    def __len__(self) -> int:
        return len(self.by_cve)

    def __contains__(self, cve: str) -> bool:
        return cve in self.by_cve

    def match_product(self, component_name: str | None) -> KisaNotice | None:
        """컴포넌트명이 보안공지 제목에 제품명으로 등장하는가 (2차 교차).

        토큰 경계로만 맞추고 3글자 이하·일반 명사는 아예 보지 않는다 — `six`가
        "Six AD Practice"에 걸리는 식의 오탐을 막는다. npm scope 이름(`@babel/core`)은
        스코프를 떼지 않고 통째로 맞춰 `core` 같은 조각 매칭을 만들지 않는다. 같은 제품
        공지가 여럿이면 **최신 공지**를 고른다(동일 날짜는 제목 사전순) — 결정론(G3) 유지.
        """
        name = (component_name or "").strip().lower()
        if len(name) < MIN_PRODUCT_NAME_LEN or name in GENERIC_NAMES:
            return None
        pattern = re.compile(rf"(?<![0-9a-z]){re.escape(name)}(?![0-9a-z])")
        matched = [notice for title, notice in self._titles if pattern.search(title)]
        if not matched:
            return None
        return max(matched, key=lambda n: (n.date, n.title))


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in _ENCODINGS:
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def _norm(cell: str) -> str:
    return cell.strip().lower().replace(" ", "")


def _map_columns(row: list[str]) -> _Columns | None:
    """첫 행이 헤더면 컬럼 역할을 돌려준다. 헤더가 아니면 None."""
    title = date = url = board = None
    skip: set[int] = set()
    for i, cell in enumerate(row):
        name = _norm(cell)
        if not name:
            continue
        if any(k in name for k in _PERSON_HEADERS):
            skip.add(i)
        elif title is None and any(k in name for k in _TITLE_HEADERS):
            title = i
        elif board is None and any(k in name for k in _BOARD_HEADERS):
            board = i
        elif date is None and any(k in name for k in _DATE_HEADERS):
            date = i
        elif url is None and any(k in name for k in _URL_HEADERS):
            url = i
    if title is None:                     # 제목을 못 찾으면 헤더로 인정하지 않는다
        return None
    return _Columns(title=title, date=date, url=url, board=board, skip=frozenset(skip))


def _at(row: list[str], index: int | None) -> str:
    if index is None or index >= len(row):
        return ""
    return row[index].strip()


def _fallback_title(cells: list[str]) -> str:
    """헤더가 없을 때 — URL·날짜·순수 숫자를 뺀 셀 중 가장 긴 것을 제목으로 본다."""
    candidates = [c.strip() for c in cells
                  if c.strip() and not _URL_RE.search(c)
                  and not _DATE_RE.fullmatch(c.strip()) and not _NUMERIC_RE.match(c.strip())]
    if not candidates:
        return ""
    return max(candidates, key=len)[:TITLE_MAX_LEN]


def load_kisa(csv_path: str | Path | None = None) -> KisaSnapshot:
    """CSV → `KisaSnapshot`. 파일이 없으면 빈 스냅샷(교차만 건너뛴다)."""
    path = Path(csv_path or settings.kisa_csv_path)
    if not path.is_file():
        log.warning("KISA 스냅샷 없음", extra={"kisa_csv_path": str(path)})
        return KisaSnapshot()

    reader = csv.reader(io.StringIO(_read_text(path)))
    header = next(reader, None)
    if header is None:
        return KisaSnapshot()
    columns = _map_columns(header)
    rows = reader if columns else chain([header], reader)
    columns = columns or _Columns()

    snapshot = KisaSnapshot()
    for row in rows:
        cells = [c for i, c in enumerate(row) if i not in columns.skip]   # 작성자 제외
        title = _at(row, columns.title)[:TITLE_MAX_LEN] or _fallback_title(cells)
        if not title:
            continue
        board = _at(row, columns.board)
        date = _at(row, columns.date) or next(
            (m.group(0) for cell in cells if (m := _DATE_RE.search(cell))), "")
        url = _at(row, columns.url) or next(
            (m.group(0) for cell in cells if (m := _URL_RE.search(cell))), "") or NOTICE_BOARD_URL
        notice = KisaNotice(title=title, url=url, date=date, board=board)

        for cve in CVE_RE.findall(" ".join(cells)):
            snapshot.by_cve.setdefault(cve, notice)   # CVE 없는 행은 자연히 걸러진다

        # 게시판 종류 컬럼이 없는 배포본은 전 행을 공지로 본다(보안공지 게시판 export 전제).
        if board == ADVISORY_BOARD or columns.board is None:
            snapshot.advisories.append(notice)
            snapshot._titles.append((title.lower(), notice))

    log.info("KISA 스냅샷 로드",
             extra={"kisa_csv_path": str(path), "cve_count": len(snapshot.by_cve),
                    "advisory_count": len(snapshot.advisories)})
    return snapshot


def kisa_snapshot_date(csv_path: str | Path | None = None) -> str:
    """스냅샷 CSV 옆의 SNAPSHOT_DATE 파일 내용 — G11 재현성 기록에 들어간다."""
    path = Path(csv_path or settings.kisa_csv_path).parent / SNAPSHOT_DATE_FILENAME
    if not path.is_file():
        return "unknown"
    return path.read_text(encoding="utf-8").strip() or "unknown"


def kisa_snapshot_label(csv_path: str | Path | None = None) -> str:
    return f"KISA-CSV@{kisa_snapshot_date(csv_path)}"
