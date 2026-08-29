"""Semgrep 러너 — subprocess + JSON 파싱 (TDD §4.2).

G13: 레지스트리 룰은 절대 쓰지 않는다(라이선스). `--config`는 항상 저장소 안의
자체 YAML 경로만 받는다. G7: 대상 코드는 실행하지 않고 정적 분석만 한다.

주의(실측): semgrep 1.139는 로그인하지 않으면 결과 JSON의 `extra.lines`와
`extra.metavars`를 "requires login"으로 가린다. 그래서 매치 내용이 필요하면
metavariable이 아니라 **워크스페이스의 해당 파일·줄을 직접 읽는다**.
"""

import json
import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from app.config import settings

log = logging.getLogger(__name__)

SEMGREP_TIMEOUT_PER_RULE = 60
SEMGREP_SUBPROCESS_TIMEOUT = 300
EXCLUDED_DIRS = ("node_modules", "venv", ".venv", "__pycache__", "dist", "build")

# node 내장 모듈 — 미선언 의존성 판정에서 제외한다.
NODE_BUILTINS = {
    "assert", "async_hooks", "buffer", "child_process", "cluster", "console", "constants",
    "crypto", "dgram", "diagnostics_channel", "dns", "domain", "events", "fs", "http", "http2",
    "https", "inspector", "module", "net", "os", "path", "perf_hooks", "process", "punycode",
    "querystring", "readline", "repl", "stream", "string_decoder", "sys", "timers", "tls",
    "trace_events", "tty", "url", "util", "v8", "vm", "wasi", "worker_threads", "zlib",
}

_MODULE_RE = re.compile(r"""(?:from|require\s*\(|import)\s*['"]([^'"]+)['"]""")


@dataclass
class RawFinding:
    check_id: str
    path: str                      # 저장소 루트 기준 상대 경로
    line: int
    message: str
    metadata: dict = field(default_factory=dict)


def semgrep_available() -> bool:
    return shutil.which("semgrep") is not None


def js_imports_rule_path() -> Path:
    return Path(settings.rules_dir) / "semgrep" / "js-imports.yaml"


def run_semgrep(root: Path, config_paths: list[str]) -> list[RawFinding]:
    """자체 룰만으로 semgrep을 돌리고 results[]를 RawFinding으로 옮긴다.

    exit 0(무발견)·1(발견) 모두 정상이며 그 외 종료 코드는 예외다.
    """
    root = Path(root)
    configs = [str(c) for c in config_paths if Path(c).exists()]
    if not configs or not semgrep_available():
        log.warning("semgrep 건너뜀", extra={"has_config": bool(configs),
                                             "semgrep_available": semgrep_available()})
        return []

    cmd = ["semgrep", "scan"]
    for c in configs:
        cmd += ["--config", c]
    cmd += ["--json", "--metrics=off", "--timeout", str(SEMGREP_TIMEOUT_PER_RULE)]
    for d in EXCLUDED_DIRS:
        cmd += ["--exclude", d]
    cmd.append(str(root))

    env = {**os.environ, "SEMGREP_ENABLE_VERSION_CHECK": "0", "SEMGREP_SEND_METRICS": "off"}
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          timeout=SEMGREP_SUBPROCESS_TIMEOUT, env=env)
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"semgrep 실행 실패(exit {proc.returncode}): {proc.stderr[-300:]}")

    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"semgrep JSON 파싱 실패: {e}") from None

    findings: list[RawFinding] = []
    for r in data.get("results") or []:
        raw_path = Path(r.get("path", ""))
        try:
            rel = raw_path.relative_to(root).as_posix()
        except ValueError:
            rel = raw_path.as_posix()
        extra = r.get("extra") or {}
        findings.append(RawFinding(
            check_id=str(r.get("check_id", "")).split(".")[-1],
            path=rel, line=int((r.get("start") or {}).get("line") or 0),
            message=str(extra.get("message") or ""),
            metadata=extra.get("metadata") or {}))
    log.info("semgrep 실행", extra={"config_count": len(configs), "result_count": len(findings),
                                    "semgrep_errors": len(data.get("errors") or [])})
    return findings


def _module_root(spec: str) -> str | None:
    """`@scope/name/sub` → `@scope/name`, `express/lib/x` → `express`, 상대경로 → None."""
    spec = spec.strip()
    if not spec or spec.startswith((".", "/")):
        return None                       # 로컬 모듈
    if spec.startswith("node:"):
        return None                       # node 내장 명시 프로토콜
    parts = spec.split("/")
    name = "/".join(parts[:2]) if spec.startswith("@") and len(parts) >= 2 else parts[0]
    return None if name in NODE_BUILTINS else name


def extract_js_imports(root: Path) -> set[str]:
    """js-imports 수집 룰의 매치 위치에서 모듈 문자열을 읽어 패키지 이름 집합을 만든다."""
    root = Path(root)
    modules: set[str] = set()
    cache: dict[str, list[str]] = {}
    for hit in run_semgrep(root, [str(js_imports_rule_path())]):
        if hit.check_id != "ansim-js-import-collect":
            continue
        lines = cache.get(hit.path)
        if lines is None:
            try:
                lines = (root / hit.path).read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                lines = []
            cache[hit.path] = lines
        if not 1 <= hit.line <= len(lines):
            continue
        for spec in _MODULE_RE.findall(lines[hit.line - 1]):
            name = _module_root(spec)
            if name:
                modules.add(name)
    return modules
