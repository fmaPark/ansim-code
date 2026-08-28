#!/usr/bin/env python3
"""Claude Code 세션 트랜스크립트(JSONL)를 마크다운 백업 파일로 내보낸다.

- 트랜스크립트 위치: ~/.claude/projects/<프로젝트-슬러그>/<세션ID>.jsonl
- 출력: <프로젝트 루트>/logs/agent/YYYY-MM-DD-{num}-{요약}.md
- 채팅 주체(사용자/Claude)와 세션 중 업데이트된 파일 목록을 명확히 표기한다.

사용 예:
    python3 export_session.py --summary "세션백업-스킬-생성" \
        --session-id 8f1b5240-9f78-44af-9c9f-409de20ef02a
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WRITE_TOOLS = {"Write": "생성/덮어쓰기", "Edit": "수정", "MultiEdit": "수정", "NotebookEdit": "수정"}

TOOL_ICONS = {
    "Bash": "💻", "Read": "📖", "Write": "✏️", "Edit": "✏️", "MultiEdit": "✏️",
    "NotebookEdit": "✏️", "Grep": "🔍", "Glob": "🔍", "WebSearch": "🌐",
    "WebFetch": "🌐", "Skill": "🧩", "Agent": "🤖", "TodoWrite": "📋",
}


def project_slug(project_dir: Path) -> str:
    return re.sub(r"[/\\_.]", "-", str(project_dir))


def find_transcript(project_dir: Path, session_id: str | None) -> Path:
    tdir = Path.home() / ".claude" / "projects" / project_slug(project_dir)
    if not tdir.is_dir():
        sys.exit(f"트랜스크립트 디렉토리를 찾을 수 없습니다: {tdir}")
    if session_id:
        p = tdir / f"{session_id}.jsonl"
        if not p.is_file():
            sys.exit(f"세션 트랜스크립트가 없습니다: {p}")
        return p
    candidates = sorted(tdir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        sys.exit(f"트랜스크립트(.jsonl)가 없습니다: {tdir}")
    return candidates[0]  # 현재 세션이 계속 기록 중이므로 최신 수정 파일이 곧 현재 세션


def to_local(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    except (ValueError, AttributeError):
        return None


def strip_injected(text: str) -> str:
    """시스템이 끼워 넣은 블록을 제거해 실제 사용자 발화만 남긴다."""
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.S)
    text = re.sub(r"<local-command-stdout>.*?</local-command-stdout>", "", text, flags=re.S)
    m = re.search(r"<command-name>(.*?)</command-name>", text, flags=re.S)
    if m:
        return f"*[명령 실행: `{m.group(1).strip()}`]*"
    return text.strip()


def describe_tool_use(block: dict) -> tuple[str, tuple[str, str] | None]:
    """도구 호출 한 줄 요약과, 파일 변경이면 (경로, 작업) 튜플을 돌려준다."""
    name = block.get("name", "?")
    inp = block.get("input", {}) or {}
    icon = TOOL_ICONS.get(name, "🔧")
    file_change = None

    if name in WRITE_TOOLS and inp.get("file_path"):
        path = inp["file_path"]
        file_change = (path, WRITE_TOOLS[name])
        detail = f"`{path}`"
    elif name == "Read" and inp.get("file_path"):
        detail = f"`{inp['file_path']}`"
    elif name == "Bash":
        desc = inp.get("description") or ""
        cmd = (inp.get("command") or "").replace("\n", " ")
        cmd = cmd if len(cmd) <= 100 else cmd[:100] + "…"
        detail = f"{desc} (`{cmd}`)" if desc else f"`{cmd}`"
    elif name == "Skill":
        detail = f"`{inp.get('skill', '')}`"
    elif name == "Agent":
        detail = inp.get("description", "")
    else:
        raw = json.dumps(inp, ensure_ascii=False)
        detail = raw if len(raw) <= 100 else raw[:100] + "…"

    return f"- {icon} **{name}** — {detail}", file_change


def parse_transcript(path: Path, include_thinking: bool):
    """JSONL을 (섹션 리스트, 파일변경 dict, 메타 dict)로 변환한다."""
    sections = []       # {"role": "user"|"claude", "ts": datetime|None, "parts": [str]}
    file_changes = {}   # path -> {"ops": set, "count": int}
    meta = {"first_ts": None, "last_ts": None, "title": None, "user_turns": 0}

    def touch_ts(ts):
        if ts is None:
            return
        if meta["first_ts"] is None:
            meta["first_ts"] = ts
        meta["last_ts"] = ts

    for line in path.open(encoding="utf-8"):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        rtype = rec.get("type")

        if rtype == "custom-title":
            meta["title"] = rec.get("title") or rec.get("customTitle") or meta["title"]
            continue
        if rtype == "summary" and rec.get("summary"):
            sections.append({"role": "system", "ts": None,
                             "items": [("text", f"*[이전 대화 요약]*\n\n{rec['summary']}")]})
            continue
        if rtype not in ("user", "assistant") or rec.get("isSidechain") or rec.get("isMeta"):
            continue

        ts = to_local(rec.get("timestamp", ""))
        content = (rec.get("message") or {}).get("content")

        if rtype == "user":
            texts = []
            has_tool_result = False
            if isinstance(content, str):
                texts.append(content)
            elif isinstance(content, list):
                for b in content:
                    if b.get("type") == "tool_result":
                        has_tool_result = True
                    elif b.get("type") == "text":
                        texts.append(b.get("text", ""))
            if has_tool_result:
                continue  # 도구 실행 결과는 대화 주체의 발화가 아니므로 본문에서 제외
            cleaned = [strip_injected(t) for t in texts]
            cleaned = [t for t in cleaned if t]
            if not cleaned:
                continue
            touch_ts(ts)
            meta["user_turns"] += 1
            sections.append({"role": "user", "ts": ts,
                             "items": [("text", t) for t in cleaned]})

        else:  # assistant — 연속 레코드는 하나의 Claude 턴으로 병합 (진행 순서 유지)
            if not isinstance(content, list):
                continue
            items = []  # ("text"|"tool", str) — 텍스트와 도구 호출을 시간순 그대로 보존
            for b in content:
                btype = b.get("type")
                if btype == "text" and b.get("text", "").strip():
                    items.append(("text", b["text"].strip()))
                elif btype == "thinking" and include_thinking and b.get("thinking", "").strip():
                    items.append(("text", f"> *(사고 과정)* {b['thinking'].strip()}"))
                elif btype == "tool_use":
                    line_txt, change = describe_tool_use(b)
                    items.append(("tool", line_txt))
                    if change:
                        p, op = change
                        entry = file_changes.setdefault(p, {"ops": set(), "count": 0})
                        entry["ops"].add(op)
                        entry["count"] += 1
            if not items:
                continue
            touch_ts(ts)
            if sections and sections[-1]["role"] == "claude":
                cur = sections[-1]
            else:
                cur = {"role": "claude", "ts": ts, "items": []}
                sections.append(cur)
            cur["items"].extend(items)

    return sections, file_changes, meta


def next_seq(out_dir: Path, date_str: str) -> int:
    pat = re.compile(rf"^{re.escape(date_str)}-(\d+)-")
    nums = [int(m.group(1)) for p in out_dir.glob(f"{date_str}-*")
            if (m := pat.match(p.name))]
    return max(nums, default=0) + 1


def sanitize_summary(s: str) -> str:
    s = re.sub(r"\s+", "-", s.strip())
    s = re.sub(r"[^\w가-힣-]", "", s)
    return re.sub(r"-{2,}", "-", s).strip("-") or "세션-백업"


def render(sections, file_changes, meta, args, transcript: Path) -> str:
    fmt = lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "-"
    lines = [f"# {args.summary} — 세션 백업", ""]
    if meta["title"]:
        lines += [f"> 세션 제목: {meta['title']}", ""]
    lines += [
        "| 항목 | 값 |",
        "|------|-----|",
        f"| 백업 일시 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |",
        f"| 세션 ID | `{transcript.stem}` |",
        f"| 프로젝트 | `{args.project_dir}` |",
        f"| 대화 시작 | {fmt(meta['first_ts'])} |",
        f"| 마지막 기록 | {fmt(meta['last_ts'])} |",
        f"| 사용자 턴 수 | {meta['user_turns']} |",
        "",
        "## 📁 업데이트된 파일",
        "",
    ]
    if file_changes:
        lines += ["| 파일 | 작업 | 횟수 |", "|------|------|------|"]
        for p, info in file_changes.items():
            ops = ", ".join(sorted(info["ops"]))
            lines.append(f"| `{p}` | {ops} | {info['count']} |")
    else:
        lines.append("*이 세션에서 파일 변경 도구(Write/Edit)로 수정된 파일이 없습니다.*")
    lines += ["", "## 💬 대화 내용", ""]

    role_header = {"user": "### 👤 사용자", "claude": "### 🤖 Claude", "system": "### ⚙️ 시스템"}
    for sec in sections:
        ts = f" — {sec['ts'].strftime('%H:%M:%S')}" if sec.get("ts") else ""
        lines += [f"{role_header[sec['role']]}{ts}", ""]
        prev_kind = None
        for kind, text in sec["items"]:
            if kind == "tool" and prev_kind != "tool":
                lines += ["**도구 호출:**", ""]  # 연속된 도구 호출은 하나의 목록으로 묶는다
            if kind == "text" and prev_kind == "tool":
                lines.append("")
            lines.append(text)
            if kind == "text":
                lines.append("")
            prev_kind = kind
        if prev_kind == "tool":
            lines.append("")
        lines += ["---", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--summary", required=True, help="파일명에 들어갈 대화 요약 슬러그 (예: 세션백업-스킬-생성)")
    ap.add_argument("--session-id", help="세션 UUID. 생략하면 최근 수정된 트랜스크립트 사용")
    ap.add_argument("--project-dir", type=Path, default=None, help="프로젝트 루트 (기본: git 루트 또는 cwd)")
    ap.add_argument("--output-dir", type=Path, default=None, help="저장 위치 (기본: <프로젝트>/logs/agent)")
    ap.add_argument("--include-thinking", action="store_true", help="assistant 사고 과정 블록 포함")
    args = ap.parse_args()

    if args.project_dir is None:
        try:
            root = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                  capture_output=True, text=True, check=True).stdout.strip()
            args.project_dir = Path(root)
        except (subprocess.CalledProcessError, FileNotFoundError):
            args.project_dir = Path.cwd()

    transcript = find_transcript(args.project_dir, args.session_id)
    sections, file_changes, meta = parse_transcript(transcript, args.include_thinking)
    if not sections:
        sys.exit("대화 내용이 비어 있습니다 — 백업할 내용이 없습니다.")

    out_dir = args.output_dir or (args.project_dir / "logs" / "agent")
    out_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    seq = next_seq(out_dir, date_str)
    out_path = out_dir / f"{date_str}-{seq}-{sanitize_summary(args.summary)}.md"

    out_path.write_text(render(sections, file_changes, meta, args, transcript), encoding="utf-8")
    print(f"백업 완료: {out_path}")
    print(f"  - 사용자 턴 {meta['user_turns']}개, 섹션 {len(sections)}개, 변경 파일 {len(file_changes)}개")


if __name__ == "__main__":
    main()
