"""gitleaks subprocess 러너 — 시크릿 룰 5종(SEC-01~05) 원천 (Task 12).

G2: RawSecret.secret_value는 마스킹(Task 14) 전까지 메모리에만 존재한다.
이 모듈은 어떤 경로에서도 시크릿 원문을 로그·예외 메시지에 싣지 않는다.
"""
import json
import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.config import settings

log = logging.getLogger(__name__)

GITLEAKS_TIMEOUT = 120  # 초 — 정적 스캔 서브프로세스 상한 (가정)

# gitleaks RuleID → 안심코드 rule_id (계획 Task 12 Interfaces 표)
_EXACT = {
    "ansim-comment-secret": "SEC-02",
    "ansim-envfile": "SEC-03",
    "ansim-kr-rrn": "SEC-05",
    "ansim-kr-phone": "SEC-05",
    "ansim-kr-account": "SEC-05",
}
_CLOUD_PREFIXES = ("aws-", "gcp-", "azure-", "google-")  # 기본 룰 중 클라우드 자격증명 → SEC-04


@dataclass(frozen=True)
class RawSecret:
    rule_id: str          # 안심코드 rule_id (SEC-01~05)
    file: str             # 저장소 루트 기준 상대 경로 (semgrep RawFinding.path와 동일 표기)
    line: int
    secret_value: str     # 원문 — 메모리 전용(G2), DB·로그 기록 금지
    match: str


def _map_rule_id(gitleaks_rule_id: str) -> str:
    if gitleaks_rule_id in _EXACT:
        return _EXACT[gitleaks_rule_id]
    if gitleaks_rule_id.startswith(_CLOUD_PREFIXES):
        return "SEC-04"
    return "SEC-01"       # 기본 룰셋 나머지 (API 키·토큰 하드코딩)


def _parse_report(entries: list[dict], root: Path) -> list[RawSecret]:
    hits = []
    for e in entries:
        # gitleaks는 -s 절대경로 기준 절대 File을 준다 — 재진단 diff 키가
        # 스캔 간 일치하도록 root 상대경로로 정규화 (semgrep 러너와 동일 표기).
        raw_path = Path(e.get("File", ""))
        try:
            rel = raw_path.relative_to(root).as_posix()
        except ValueError:
            rel = raw_path.as_posix()
        hits.append(RawSecret(
            rule_id=_map_rule_id(e.get("RuleID", "")),
            file=rel,
            line=int(e.get("StartLine", 0)),
            secret_value=e.get("Secret", ""),
            match=e.get("Match", ""),
        ))
    return hits


def config_path() -> Path:
    return Path(settings.rules_dir) / "gitleaks" / "ansim.toml"


def run_gitleaks(root: Path) -> list[RawSecret]:
    """exit 0=무발견, 1=발견 — 둘 다 정상. 그 외 exit는 RuntimeError."""
    root = Path(root)
    with tempfile.TemporaryDirectory(prefix="ansim-gitleaks-") as td:
        report = str(Path(td) / "report.json")
        cmd = ["gitleaks", "detect", "--no-git",
               "-s", str(root), "-c", str(config_path()),
               "-f", "json", "-r", report]
        r = subprocess.run(cmd, capture_output=True, timeout=GITLEAKS_TIMEOUT)
        if r.returncode not in (0, 1):
            # stderr에는 설정 오류 등만 실린다 — 시크릿 원문은 리포트 파일에만 있다(G2).
            raise RuntimeError(f"gitleaks 실패 (exit {r.returncode}): {r.stderr.decode()[:200]}")
        try:
            entries = json.loads(Path(report).read_text() or "[]")
        except (OSError, json.JSONDecodeError):
            entries = []
        hits = _parse_report(entries or [], root)
        log.info("gitleaks done", extra={"findings": len(hits), "exit": r.returncode})
        return hits
