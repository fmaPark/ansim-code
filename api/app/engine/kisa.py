"""KISA 보호나라(KrCERT) 보안공지 스냅샷 로더 + CVE 교차 (TDD §4.6).

컬럼명에 의존하지 않는다 — 배포본의 컬럼 구성이 바뀔 수 있어 행 전체를 문자열로
합쳐 CVE ID를 뽑고, 링크·날짜·제목은 셀의 형태로 판별한다.
"""

import csv
import io
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from app.config import settings

log = logging.getLogger(__name__)

CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}")
_URL_RE = re.compile(r"https?://\S+")
_DATE_RE = re.compile(r"\d{4}[-./]\d{1,2}[-./]\d{1,2}")
_ENCODINGS = ("utf-8-sig", "cp949")      # data.go.kr 배포본이 EUC-KR(cp949)인 경우 대비

SNAPSHOT_DATE_FILENAME = "SNAPSHOT_DATE"


@dataclass
class KisaNotice:
    title: str
    url: str
    date: str


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in _ENCODINGS:
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def load_kisa(csv_path: str | Path | None = None) -> dict[str, KisaNotice]:
    """CSV → {CVE ID: KisaNotice}. 파일이 없으면 빈 dict(교차만 건너뛴다)."""
    path = Path(csv_path or settings.kisa_csv_path)
    if not path.is_file():
        log.warning("KISA 스냅샷 없음", extra={"kisa_csv_path": str(path)})
        return {}

    notices: dict[str, KisaNotice] = {}
    reader = csv.reader(io.StringIO(_read_text(path)))
    for row in reader:
        joined = " ".join(row)
        cves = CVE_RE.findall(joined)
        if not cves:
            continue                       # 헤더 행·CVE 없는 공지는 자연히 걸러진다
        url = next((m.group(0) for cell in row if (m := _URL_RE.search(cell))), "")
        date = next((m.group(0) for cell in row if (m := _DATE_RE.search(cell))), "")
        title = next((cell.strip() for cell in row
                      if cell.strip() and not _URL_RE.search(cell) and not _DATE_RE.search(cell)
                      and not CVE_RE.search(cell)), "")
        notice = KisaNotice(title=title, url=url, date=date)
        for cve in cves:
            notices.setdefault(cve, notice)

    log.info("KISA 스냅샷 로드", extra={"kisa_csv_path": str(path), "cve_count": len(notices)})
    return notices


def kisa_snapshot_date(csv_path: str | Path | None = None) -> str:
    """스냅샷 CSV 옆의 SNAPSHOT_DATE 파일 내용 — G11 재현성 기록에 들어간다."""
    path = Path(csv_path or settings.kisa_csv_path).parent / SNAPSHOT_DATE_FILENAME
    if not path.is_file():
        return "unknown"
    return path.read_text(encoding="utf-8").strip() or "unknown"


def kisa_snapshot_label(csv_path: str | Path | None = None) -> str:
    return f"KISA-CSV@{kisa_snapshot_date(csv_path)}"
