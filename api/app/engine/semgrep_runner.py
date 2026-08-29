"""semgrep subprocess 러너 (Task 11 인터페이스의 M4 선작성분 — 계획 M4 트랙 주석 참조).

자체 YAML(rules/semgrep/*.yaml)만 사용한다 — 레지스트리 룰 미사용(G13).
M3 트랙(Task 11)이 SCA용 러너를 병합할 때 이 모듈과 통합한다(충돌 예상 지점).
"""
import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.config import settings

log = logging.getLogger(__name__)

SEMGREP_TIMEOUT = 300  # 초 (가정 — G14 2분 목표의 하위 예산)


@dataclass(frozen=True)
class SemgrepHit:
    ansim_rule: str       # 카탈로그 rule_id (metadata.ansim_rule)
    semgrep_id: str
    file: str
    line: int
    message: str
    evidence: str         # 매칭 라인 원문 — 저장 전 반드시 마스킹(G2)


def rules_path() -> Path:
    return Path(settings.rules_dir) / "semgrep"


def _parse_results(results: list[dict], root: Path) -> list[SemgrepHit]:
    hits = []
    for r in results:
        meta = (r.get("extra") or {}).get("metadata") or {}
        ansim = meta.get("ansim_rule")
        if not ansim:
            continue                      # 자체 룰이 아니면 무시 (G13 방어)
        path = r.get("path", "")
        try:
            path = str(Path(path).relative_to(root))
        except ValueError:
            pass
        hits.append(SemgrepHit(
            ansim_rule=str(ansim),
            semgrep_id=r.get("check_id", ""),
            file=path,
            line=int((r.get("start") or {}).get("line", 0)),
            message=(r.get("extra") or {}).get("message", ""),
            evidence=(r.get("extra") or {}).get("lines", ""),
        ))
    return hits


def run_semgrep(root: Path, config: Path | None = None) -> list[SemgrepHit]:
    cmd = ["semgrep", "scan", "--json", "--quiet",
           "--metrics=off", "--disable-version-check",
           "--config", str(config or rules_path()), str(root)]
    r = subprocess.run(cmd, capture_output=True, timeout=SEMGREP_TIMEOUT)
    # semgrep exit: 0=무발견/발견 무관 성공(기본), 1=발견(--error 시)·기타 오류 — JSON 유무로 판정
    try:
        payload = json.loads(r.stdout.decode() or "{}")
    except json.JSONDecodeError:
        raise RuntimeError(f"semgrep 실패 (exit {r.returncode}): {r.stderr.decode()[:200]}") from None
    hits = _parse_results(payload.get("results", []), root)
    log.info("semgrep done", extra={"findings": len(hits), "exit": r.returncode})
    return hits
