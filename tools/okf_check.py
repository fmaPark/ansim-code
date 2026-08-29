#!/usr/bin/env python3
"""OKF v0.2 번들 적합성 + 링크·앵커 점검.

사용법: python3 tools/okf_check.py [번들경로]   (기본값: docs)

점검 항목
  1. 적합성(SPEC §11) — 예약 파일이 아닌 모든 .md에 파싱 가능한 YAML frontmatter가 있고
     `type`이 비어 있지 않은가. 예약 파일(index.md·log.md)이 §8·§9 구조를 지키는가.
  2. 링크 — 문서 간 상대 링크의 대상 파일이 실제로 존재하는가.
  3. 앵커 — `#조항` 링크가 대상 문서의 제목에서 생성되는 슬러그와 일치하는가.
"""
import re, sys, pathlib

RESERVED = {"index.md", "log.md"}

def slug(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.strip().lower(), flags=re.UNICODE)
    return re.sub(r"\s+", "-", s)

def split_front_matter(text: str):
    """(frontmatter 원문 | None, 본문) 반환."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text          # 닫히지 않음 → 파싱 실패로 취급
    return text[4:end], text[end + 4:]

def parse_yaml(raw: str):
    try:
        import yaml
        return yaml.safe_load(raw), None
    except ImportError:
        keys = dict(re.findall(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", raw, re.M))
        return keys, None
    except Exception as e:
        return None, str(e)

def headings(text: str):
    """코드 펜스 밖의 제목만 수집."""
    out, fenced = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced:
            m = re.match(r"^(#{1,6})\s+(.*?)\s*$", line)
            if m:
                out.append(m.group(2))
    return out

def main(root_arg="docs"):
    root = pathlib.Path(root_arg)
    if not root.is_dir():
        print(f"오류: 번들 디렉토리를 찾을 수 없음 — {root}"); return 2

    md = sorted(root.rglob("*.md"))
    anchors = {p: {slug(h) for h in headings(p.read_text(encoding="utf-8"))} for p in md}
    errors, warnings, checked_links = [], [], 0

    for p in md:
        rel, text = p.relative_to(root), p.read_text(encoding="utf-8")
        raw, body = split_front_matter(text)

        # --- 1. 적합성 ---
        if p.name in RESERVED:
            is_bundle_root_index = (p.parent == root and p.name == "index.md")
            if raw is not None and not is_bundle_root_index:
                errors.append(f"{rel}: 예약 파일에는 frontmatter를 둘 수 없다(번들 루트 index.md의 okf_version만 예외)")
            if raw is not None and is_bundle_root_index:
                data, err = parse_yaml(raw)
                if err or not isinstance(data, dict):
                    errors.append(f"{rel}: frontmatter YAML 파싱 실패 — {err}")
                elif "okf_version" not in data:
                    warnings.append(f"{rel}: 번들 루트 index.md에 okf_version 없음")
            if p.name == "log.md" and not re.search(r"^##\s+\d{4}-\d{2}-\d{2}\s*$", body or text, re.M):
                errors.append(f"{rel}: log.md에 `## YYYY-MM-DD` 날짜 묶음이 없다(SPEC §9)")
        else:
            if raw is None:
                errors.append(f"{rel}: frontmatter 없음(SPEC §11 조건 1)")
                continue
            data, err = parse_yaml(raw)
            if err or not isinstance(data, dict):
                errors.append(f"{rel}: frontmatter YAML 파싱 실패 — {err}")
                continue
            if not str(data.get("type", "")).strip():
                errors.append(f"{rel}: `type`이 비어 있음(SPEC §11 조건 2)")
            for f in ("title", "description"):
                if not str(data.get(f, "")).strip():
                    warnings.append(f"{rel}: 권장 필드 `{f}` 없음")

        # --- 2·3. 링크와 앵커 ---
        for target in re.findall(r"\]\(([^)\s]+)\)", body if raw is not None else text):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path_part, _, frag = target.partition("#")
            if not path_part.endswith(".md"):
                continue
            dest = (p.parent / path_part).resolve()
            checked_links += 1
            if not dest.exists():
                errors.append(f"{rel}: 링크 대상 없음 — {target}")
            elif frag and dest in anchors and frag not in anchors[dest]:
                errors.append(f"{rel}: 앵커 없음 — {target}")

    print(f"번들: {root}  |  문서 {len(md)}건  |  검사한 내부 링크 {checked_links}건")
    for w in warnings:
        print(f"  경고  {w}")
    for e in errors:
        print(f"  오류  {e}")
    if errors:
        print(f"\n실패 — 오류 {len(errors)}건")
        return 1
    print(f"\n통과 — OKF v0.2 적합" + (f" (경고 {len(warnings)}건)" if warnings else ""))
    return 0

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:2]))
