import os
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path

from app.config import OS_JUNK_FILES, SKIP_DIRS, settings


class ValidationError(Exception):
    pass


@dataclass
class IngestResult:
    root: Path
    commit_hash: str | None


def ingest_git(url: str, workdir: Path) -> IngestResult:
    if not url.startswith("https://"):
        raise ValidationError("공개 https git URL만 지원합니다")
    dst = workdir / "repo"
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}   # 공개 repo만 — 인증 프롬프트 차단
    r = subprocess.run(["git", "clone", "--depth", "1", "--single-branch", url, str(dst)],
                       capture_output=True, timeout=settings.git_clone_timeout, env=env)
    if r.returncode != 0:
        raise ValidationError(f"clone 실패: {r.stderr.decode()[:200]}")
    commit = subprocess.run(["git", "-C", str(dst), "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    return IngestResult(root=dst, commit_hash=commit)


def _skippable(parts: tuple[str, ...], name: str) -> bool:
    return bool(set(parts) & SKIP_DIRS) or name in OS_JUNK_FILES


def ingest_zip(upload_path: Path, workdir: Path) -> IngestResult:
    if upload_path.stat().st_size > settings.max_zip_bytes:
        raise ValidationError("zip은 50MB 이하만 지원합니다")
    dst = workdir / "src"
    dst.mkdir()
    total, count = 0, 0
    try:
        zf = zipfile.ZipFile(upload_path)
    except zipfile.BadZipFile:
        raise ValidationError("올바른 zip 파일이 아닙니다") from None
    with zf:
        for info in zf.infolist():
            p = Path(info.filename)
            if info.is_dir():
                continue
            if p.is_absolute() or ".." in p.parts:
                raise ValidationError(f"경로 위반: {info.filename}")   # path traversal
            if (info.external_attr >> 16) & 0o120000 == 0o120000:
                continue  # symlink 무시
            if _skippable(p.parts, p.name):
                continue
            count += 1
            total += info.file_size
            if count > settings.max_extracted_files:
                raise ValidationError("파일 수 상한 초과")
            if total > settings.max_extracted_bytes:
                raise ValidationError("해제 크기 상한 초과")
            target = dst / p
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as s, open(target, "wb") as d:
                d.write(s.read(min(info.file_size + 1, settings.max_extracted_bytes)))
    return IngestResult(root=dst, commit_hash=None)
