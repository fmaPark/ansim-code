#!/usr/bin/env python3
"""ansim-benchmark TPR·FPR 측정 — 명세 docs/benchmark-spec.md §5.1 (계획 Task 26 Step 4).

안심코드 API에 벤치마크 저장소를 스캔시키고, 돌아온 finding을 오라클
(`verification/expected_findings.yaml`)과 대조해 **TPR·FPR·부가 발견 3단 표**를 만든다.

매칭은 오라클 dict와 finding 목록만 받는 순수 함수(`measure`)에 모여 있다.
오라클 YAML만 바꿔도 재실행되고, API 없이 단위 테스트할 수 있다.

사용:
    python verification/measure_detection.py \\
        --api http://localhost:8000 \\
        --repo https://github.com/fmaPark/ansim-benchmark \\
        --oracle /path/to/expected_findings.yaml

    # 로컬 반복 확인용 — git push 없이 zip으로 같은 측정
    python verification/measure_detection.py --api ... --zip bench.zip --oracle ...
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

# ── 룰별 오라클 키 (명세 §1.1 — 러너의 finding 방출 규약과 1:1) ────────────────
COMPONENT_KEY_RULES = {f"SCA-0{n}" for n in range(1, 10)}          # (rule_id, package)
DECLARED_IN_RULES = {"SCA-10", "SCA-11", "SCA-12"}                 # (rule_id, declared_in)
REPO_WIDE_RULES = {"P1", "P8", "P9"}                               # (rule_id) — file=None
# 나머지(SEC-01~05, P2~P7, P10, AUX-01~04)는 (rule_id, file) 키다.

# FPR 분모·분자에서 제외한다. 저장소 전체 "부재" 판정이라 같은 트리에 음성을 둘 수 없다
# (명세 §1.2) — 이들의 오탐은 Task 27의 PyGoat·dogfooding에서 측정한다.
REPO_WIDE_FPR_EXCLUDED = {"P8", "P9", "P10"}

ALL_RULES = (
    [f"SCA-{n:02d}" for n in range(1, 13)]
    + [f"SEC-{n:02d}" for n in range(1, 6)]
    + [f"P{n}" for n in range(1, 11)]
    + [f"AUX-{n:02d}" for n in range(1, 5)]
)

BENCHMARK_DIRS = ("vulnerable/", "clean/")

# 미기입 센티넬 — 하나라도 남으면 측정을 시작하지 않는다(fail-closed).
SENTINEL_RE = re.compile(r"^\s*(TBD|<.*>)\s*$", re.I)

# SCA finding의 evidence에서 컴포넌트명을 뽑는다.
#   SCA-01: "미선언 의존성: 코드가 `redis`을(를) import 하지만 …"      (sca_rules.py:92)
#   SCA-02~09: "django 3.2.12 — …" / "flask-cors (버전 미상) — …"      (sca_rules.py:46)
_BACKTICK_RE = re.compile(r"`([^`]+)`")
_LABEL_RE = re.compile(r"^(.*?)\s+(?:\(버전 미상\)|\S+)\s+—\s")


def canon(name: str) -> str:
    """api/app/engine/repo_checks.py:26의 정규화와 같은 규칙."""
    return re.sub(r"[-_.]+", "-", name).lower()


def package_of(finding: dict) -> str | None:
    """SCA finding의 evidence → 컴포넌트 이름(정규화). 못 뽑으면 None."""
    evidence = finding.get("evidence") or ""
    if finding.get("rule_id") == "SCA-01":
        match = _BACKTICK_RE.search(evidence)
        return canon(match.group(1)) if match else None
    match = _LABEL_RE.match(evidence)
    return canon(match.group(1)) if match else None


# ── 오라클 ────────────────────────────────────────────────────────────────────
def load_oracle(path: Path) -> dict:
    """expected_findings.yaml 로드. PyYAML이 없으면 최소 파서로 읽는다."""
    text = path.read_text(encoding="utf-8")
    try:
        import yaml
    except ModuleNotFoundError:
        return _parse_oracle_fallback(text)
    return yaml.safe_load(text)


def _parse_oracle_fallback(text: str) -> dict:
    """`- { ... }` 흐름 매핑만 쓰는 오라클 서식 전용 최소 파서(PyYAML 부재 시)."""
    positives, negatives, section = [], [], None
    buffer = ""
    for raw in text.splitlines():
        line = raw.split(" #", 1)[0].rstrip() if not raw.lstrip().startswith("#") else ""
        if not line.strip():
            continue
        if line.startswith("positives:"):
            section = "positives"
            continue
        if line.startswith("negatives_expect_no_confirmed:"):
            section = "negatives"
            continue
        stripped = line.strip()
        if section == "negatives" and stripped.startswith("- "):
            negatives.append(stripped[2:].strip())
            continue
        if section != "positives":
            continue
        buffer = (buffer + " " + stripped) if buffer else stripped
        if buffer.count("{") and buffer.count("{") == buffer.count("}"):
            positives.append(_parse_flow_map(buffer))
            buffer = ""
    return {"positives": positives, "negatives_expect_no_confirmed": negatives}


def _parse_flow_map(item: str) -> dict:
    body = item[item.index("{") + 1:item.rindex("}")]
    entry: dict = {}
    for part in re.split(r",(?=(?:[^\"']*[\"'][^\"']*[\"'])*[^\"']*$)", body):
        if ":" not in part:
            continue
        key, _, value = part.partition(":")
        value = value.strip().strip('"').strip("'")
        if value == "null":
            parsed: object = None
        elif re.fullmatch(r"-?\d+", value):
            parsed = int(value)
        else:
            parsed = value
        entry[key.strip()] = parsed
    return entry


def sentinel_violations(oracle: dict) -> list[str]:
    """미기입 센티넬 검사 — 남아 있으면 그 룰이 조용히 TPR 0으로 집계된다.

    Step 2에서 기입을 빠뜨린 것과 진짜 룰 갭을 구분할 수 없게 되므로,
    측정을 시작하지 않고 중단한다(PR #12 리뷰 수락 제안).
    """
    problems: list[str] = []
    for entry in oracle.get("positives") or []:
        rule_id = entry.get("rule_id", "?")
        where = entry.get("file") or entry.get("package") or "(repo-wide)"
        for field in ("file", "package", "line", "note"):
            value = entry.get(field)
            if isinstance(value, str) and SENTINEL_RE.match(value):
                problems.append(f"{rule_id} {where}: `{field}: {value}` 미기입 센티넬")
        if "package" not in entry and rule_id not in REPO_WIDE_RULES:
            if "file" not in entry:
                problems.append(f"{rule_id}: file·package 어느 키도 없다")
            elif "line" not in entry and rule_id not in DECLARED_IN_RULES:
                # SCA-10·11·12는 매니페스트 경로가 키라 line을 애초에 방출하지 않는다.
                problems.append(f"{rule_id} {where}: `line` 필드 자체가 없다"
                                " (파일 단위 룰이면 `line: null`로 명시할 것)")
    return problems


# ── 매칭 (순수 함수) ──────────────────────────────────────────────────────────
def oracle_key(entry: dict) -> tuple:
    rule_id = entry["rule_id"]
    if rule_id in REPO_WIDE_RULES:
        return (rule_id,)
    if rule_id in COMPONENT_KEY_RULES:
        return (rule_id, canon(str(entry.get("package") or "")))
    return (rule_id, entry.get("file"))


def finding_key(finding: dict) -> tuple | None:
    """finding → 오라클 키. 키를 만들 수 없으면 None."""
    rule_id = finding.get("rule_id")
    if rule_id in REPO_WIDE_RULES:
        return (rule_id,)
    if rule_id in COMPONENT_KEY_RULES:
        package = package_of(finding)
        return (rule_id, package) if package else None
    return (rule_id, finding.get("file_path"))


def in_benchmark_scope(finding: dict) -> bool:
    """사후 필터 — 스캔은 저장소 전체가 대상이라 여기서 범위를 좁힌다(명세 §1.1 B5).

    repo-wide 룰과 컴포넌트 키 룰은 file_path가 없으므로 예외로 통과시킨다.
    """
    rule_id = finding.get("rule_id")
    if rule_id in REPO_WIDE_RULES or rule_id in COMPONENT_KEY_RULES:
        return True
    path = finding.get("file_path") or ""
    return path.startswith(BENCHMARK_DIRS)


def measure(oracle: dict, findings: list[dict], clean_file_count: int) -> dict:
    """오라클 × finding → TPR·FPR·부가 발견. API도 파일 시스템도 건드리지 않는다."""
    expected = oracle.get("positives") or []
    scoped = [f for f in findings if in_benchmark_scope(f)]

    detected_keys: set[tuple] = set()
    for finding in scoped:
        key = finding_key(finding)
        if key:
            detected_keys.add(key)

    # TPR — 룰별 기대/검출
    per_rule: dict[str, dict] = {}
    for entry in expected:
        rule_id = entry["rule_id"]
        slot = per_rule.setdefault(rule_id, {"expected": 0, "hit": 0, "missed": []})
        slot["expected"] += 1
        where = entry.get("file") or entry.get("package") or "(repo-wide)"
        if oracle_key(entry) in detected_keys:
            slot["hit"] += 1
        else:
            slot["missed"].append(where)

    # FPR — clean/에서 나온 confirmed. repo-wide 룰은 분모·분자 모두에서 제외(§1.2).
    false_positives = [
        f for f in findings
        if (f.get("file_path") or "").startswith("clean/")
        and f.get("status") == "confirmed"
        and f.get("rule_id") not in REPO_WIDE_FPR_EXCLUDED
    ]

    # 부가 발견 — vulnerable/에서 나온 confirmed 중 오라클에도 대표 키잉에도 없는 것.
    expected_keys = {oracle_key(e) for e in expected}
    expected_rules = {e["rule_id"] for e in expected}
    extras: list[dict] = []
    for finding in scoped:
        if finding.get("status") != "confirmed":
            continue
        path = finding.get("file_path") or ""
        if path.startswith("clean/"):
            continue                       # 오탐으로 이미 셌다
        key = finding_key(finding)
        if key in expected_keys:
            continue
        # 대표 키잉 + 다발 허용(§5.1): 같은 룰의 추가 발화는 오탐이 아니다.
        extras.append({
            "rule_id": finding.get("rule_id"),
            "where": path or (package_of(finding) or "(repo-wide)"),
            "evidence": (finding.get("evidence") or "")[:80],
            "same_rule_as_expected": finding.get("rule_id") in expected_rules,
        })

    return {
        "per_rule": per_rule,
        "false_positives": false_positives,
        "clean_file_count": clean_file_count,
        "extras": extras,
        "grade": None,
    }


# ── API 호출 ──────────────────────────────────────────────────────────────────
def _request(url: str, *, data: bytes | None = None, headers: dict | None = None,
             timeout: int = 60) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:      # noqa: S310 (로컬 API)
        return json.loads(resp.read().decode("utf-8"))


def _multipart(zip_path: Path) -> tuple[bytes, str]:
    boundary = f"----ansim{uuid.uuid4().hex}"
    head = (f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{zip_path.name}"\r\n'
            f"Content-Type: application/zip\r\n\r\n").encode()
    tail = f"\r\n--{boundary}--\r\n".encode()
    return head + zip_path.read_bytes() + tail, f"multipart/form-data; boundary={boundary}"


def run_scan(api: str, *, repo: str | None, zip_path: Path | None,
             poll_seconds: int = 5, timeout_seconds: int = 900) -> tuple[dict, float]:
    """스캔 1회 실행 → (dev 리포트, 소요 초). 실패하면 RuntimeError."""
    if zip_path:
        body, content_type = _multipart(zip_path)
        started = time.monotonic()
        created = _request(f"{api}/api/scans", data=body, headers={"Content-Type": content_type},
                           timeout=300)
    else:
        started = time.monotonic()
        created = _request(f"{api}/api/scans", data=json.dumps({"git_url": repo}).encode(),
                           headers={"Content-Type": "application/json"})
    scan_id = created["scan_id"]
    print(f"  스캔 {scan_id} 시작", flush=True)

    while True:
        status = _request(f"{api}/api/scans/{scan_id}")
        if status["status"] == "done":
            elapsed = time.monotonic() - started
            break
        if status["status"] == "failed":
            raise RuntimeError(f"스캔 실패: {status.get('error_message')}")
        if time.monotonic() - started > timeout_seconds:
            raise RuntimeError(f"스캔이 {timeout_seconds}초 안에 끝나지 않았다")
        print(f"    {status['status']} / {status.get('current_stage')}", flush=True)
        time.sleep(poll_seconds)

    report = _request(f"{api}/api/scans/{scan_id}/report?mode=dev")
    report["_scan_id"] = scan_id
    return report, elapsed


# ── 리포트 ────────────────────────────────────────────────────────────────────
def render(result: dict, *, source: str, grade: str, elapsed: float,
           provenance: dict, gaps: dict[str, str]) -> str:
    """docs/measurements.md에 그대로 붙일 수 있는 3단 표."""
    per_rule = result["per_rule"]
    lines: list[str] = []
    lines.append(f"측정 대상: `{source}` · 등급 **{grade}** · 소요 {elapsed:.1f}s")
    lines.append("")
    lines.append(f"- `content_fingerprint`: `{provenance.get('content_fingerprint', '')[:16]}…`"
                 f" ({provenance.get('fingerprint_type')})")
    lines.append(f"- `rule_catalog_version`: `{provenance.get('rule_catalog_version')}`")
    lines.append(f"- `vuln_db_snapshot_date`: {provenance.get('vuln_db_snapshot_date')}")
    lines.append(f"- `llm_model_id`: {provenance.get('llm_model_id') or '(LLM 미호출)'}")
    lines.append("")

    total_expected = sum(v["expected"] for v in per_rule.values())
    total_hit = sum(v["hit"] for v in per_rule.values())
    lines.append("#### ① TPR — 룰별 검출률 (전체 31종 기준)")
    lines.append("")
    lines.append("| 룰 | 기대 | 검출 | TPR | 미검출 위치 / 사유 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for rule_id in ALL_RULES:
        slot = per_rule.get(rule_id)
        if not slot:
            lines.append(f"| {rule_id} | 0 | — | — | 벤치마크 미시연 |")
            continue
        expected, hit = slot["expected"], slot["hit"]
        tpr = f"{hit / expected * 100:.0f}%" if expected else "—"
        note = ", ".join(slot["missed"])
        if slot["missed"] and rule_id in gaps:
            note = f"{note} — {gaps[rule_id]}"
        mark = "" if hit == expected else " ⚠"
        lines.append(f"| {rule_id}{mark} | {expected} | {hit} | {tpr} | {note} |")
    overall = f"{total_hit / total_expected * 100:.1f}%" if total_expected else "—"
    lines.append(f"| **합계** | **{total_expected}** | **{total_hit}** | **{overall}** | |")
    lines.append("")

    clean_count = result["clean_file_count"]
    fps = result["false_positives"]
    rate = f"{len(fps) / clean_count * 100:.1f}%" if clean_count else "—"
    lines.append("#### ② FPR — `clean/` 오탐률")
    lines.append("")
    lines.append(f"clean 파일 {clean_count}개 중 confirmed 발생 **{len(fps)}건** → FPR **{rate}**")
    lines.append("")
    lines.append("| 룰 | 파일 | 근거 |")
    lines.append("| --- | --- | --- |")
    if fps:
        for finding in fps:
            lines.append(f"| {finding['rule_id']} | `{finding['file_path']}` | "
                         f"{(finding.get('evidence') or '')[:60]} |")
    else:
        lines.append("| — | — | 오탐 없음 |")
    lines.append("")
    lines.append("> repo-wide 룰(P8·P9·P10)은 분모·분자에서 제외했다 — 같은 스캔 트리에 음성을 둘 수 "
                 "없어서다(명세 §1.2). 이들의 오탐은 Task 27(PyGoat·dogfooding)에서 측정한다.")
    lines.append("")

    extras = result["extras"]
    lines.append("#### ③ 부가 발견 — 오라클 밖 confirmed (지표 미집계)")
    lines.append("")
    grouped: dict[str, list[dict]] = {}
    for extra in extras:
        grouped.setdefault(extra["rule_id"], []).append(extra)
    lines.append("| 룰 | 건수 | 위치(발췌) | 성격 |")
    lines.append("| --- | --- | --- | --- |")
    if grouped:
        for rule_id in sorted(grouped):
            items = grouped[rule_id]
            where = ", ".join(sorted({str(i["where"]) for i in items})[:4])
            kind = "동일 룰의 추가 발화(다발 허용)" if items[0]["same_rule_as_expected"] \
                else "오라클에 없는 룰의 발화"
            lines.append(f"| {rule_id} | {len(items)} | {where} | {kind} |")
    else:
        lines.append("| — | 0 | — | 부가 발견 없음 |")
    lines.append("")
    lines.append("> 명세 §5.1: `vulnerable/`에서 나온 confirmed 중 오라클에도 대표 키잉 집합에도 "
                 "없는 발견은 TPR·FPR 어느 지표에도 세지 않고 여기에 공개한다.")
    return "\n".join(lines)


def count_clean_files(benchmark_root: Path | None) -> int:
    if not benchmark_root or not benchmark_root.is_dir():
        return 0
    clean = benchmark_root / "clean"
    if not clean.is_dir():
        return 0
    return sum(1 for p in clean.rglob("*") if p.is_file() and not p.name.startswith("."))


def main() -> int:
    parser = argparse.ArgumentParser(description="ansim-benchmark TPR·FPR 측정 (명세 §5.1)")
    parser.add_argument("--api", default="http://localhost:8000", help="안심코드 API 베이스 URL")
    parser.add_argument("--repo", help="벤치마크 공개 git URL")
    parser.add_argument("--zip", dest="zip_path", type=Path, help="git 대신 zip으로 측정(로컬 반복용)")
    parser.add_argument("--oracle", type=Path, required=True,
                        help="expected_findings.yaml 경로")
    parser.add_argument("--benchmark-root", type=Path,
                        help="clean/ 파일 수를 셀 로컬 체크아웃 경로(FPR 분모)")
    parser.add_argument("--out", type=Path, help="표를 파일로도 저장")
    parser.add_argument("--gap-note", action="append", default=[], metavar="RULE=사유",
                        help="미검출 룰의 해석을 표에 병기한다(여러 번 지정 가능). "
                             "미검출이 벤치마크 결함인지 룰 갭인지는 측정이 아니라 사람의 판단이다")
    args = parser.parse_args()

    if not args.repo and not args.zip_path:
        parser.error("--repo 또는 --zip 중 하나는 필요하다")

    oracle = load_oracle(args.oracle)

    # fail-closed — 미기입 센티넬이 남아 있으면 측정하지 않는다.
    problems = sentinel_violations(oracle)
    if problems:
        print(f"오라클에 미기입 항목 {len(problems)}건 — 측정을 시작하지 않는다:\n", file=sys.stderr)
        for line in problems:
            print(f"  - {line}", file=sys.stderr)
        print("\n이 상태로 측정하면 해당 룰이 조용히 TPR 0으로 집계되어 룰 갭과 구분되지 않는다.",
              file=sys.stderr)
        return 2

    source = args.repo or str(args.zip_path)
    print(f"측정 시작 — {source}")
    try:
        report, elapsed = run_scan(args.api, repo=args.repo, zip_path=args.zip_path)
    except (urllib.error.URLError, RuntimeError) as exc:
        print(f"스캔 실패: {exc}", file=sys.stderr)
        return 3

    clean_count = count_clean_files(args.benchmark_root)
    result = measure(oracle, report.get("findings") or [], clean_count)

    gaps: dict[str, str] = {}
    for note in args.gap_note:
        rule_id, _, reason = note.partition("=")
        gaps[rule_id.strip()] = reason.strip()
    table = render(result, source=source, grade=report.get("grade", "?"), elapsed=elapsed,
                   provenance=report.get("provenance") or {}, gaps=gaps)
    print()
    print(table)
    if args.out:
        args.out.write_text(table + "\n", encoding="utf-8")
        print(f"\n표를 {args.out}에 저장했다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
