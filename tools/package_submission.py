#!/usr/bin/env python3
"""제출용 소스 아카이브 생성 (계획 Task 28 Step 4).

`git archive --format=zip`을 그대로 쓰면 `협의체_기록/` 같은 한글 경로에서 문제가 생긴다.
git이 파일명을 UTF-8 바이트로 넣으면서 zip 헤더의 EFS 플래그(bit 11)를 세우지 않아,
Info-ZIP `unzip`이 이름을 CP437로 읽고 "Illegal byte sequence"로 해제를 멈춘다.
macOS Finder·`tar`·Python은 열리지만 심사 환경이 `unzip`이면 거기서 막힌다.

그래서 git이 만든 tar를 받아 **Python zipfile로 다시 싼다** — zipfile은 비ASCII 이름에
UTF-8 플래그를 자동으로 세운다. 추적 파일만 담으므로 `.env`·`node_modules`는 들어가지 않는다.

    python3 tools/package_submission.py                    # dist/ansim-code-<sha>.zip
    python3 tools/package_submission.py --ref v1.0 --out /tmp/submission.zip
"""

import argparse
import io
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path


def build(ref: str, out: Path, prefix: str) -> tuple[int, int]:
    tar_bytes = subprocess.run(
        ["git", "archive", "--format=tar", f"--prefix={prefix}", ref],
        check=True, capture_output=True).stdout

    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tar, \
            zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for member in tar:
            if not member.isfile():
                continue
            payload = tar.extractfile(member)
            if payload is None:
                continue
            info = zipfile.ZipInfo(member.name)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (member.mode & 0xFFFF) << 16
            zf.writestr(info, payload.read())
            count += 1
    return count, out.stat().st_size


def main() -> int:
    parser = argparse.ArgumentParser(description="제출용 소스 zip 생성 (한글 경로 안전)")
    parser.add_argument("--ref", default="HEAD", help="아카이브할 git ref (기본 HEAD)")
    parser.add_argument("--out", type=Path, help="출력 경로 (기본 dist/ansim-code-<sha>.zip)")
    parser.add_argument("--prefix", help="아카이브 안 최상위 디렉토리 (기본 ansim-code/)")
    args = parser.parse_args()

    sha = subprocess.run(["git", "rev-parse", "--short", args.ref],
                         check=True, capture_output=True, text=True).stdout.strip()
    prefix = args.prefix or "ansim-code/"
    if not prefix.endswith("/"):
        prefix += "/"
    out = args.out or Path("dist") / f"ansim-code-{sha}.zip"

    count, size = build(args.ref, out, prefix)
    print(f"{out} — 파일 {count}개, {size / 1024:.0f}KB (ref {args.ref} @ {sha})")

    with zipfile.ZipFile(out) as zf:
        non_ascii = [n for n in zf.namelist() if not n.isascii()]
    print(f"비ASCII 경로 {len(non_ascii)}개 — UTF-8 플래그로 기록됨")
    return 0


if __name__ == "__main__":
    sys.exit(main())
