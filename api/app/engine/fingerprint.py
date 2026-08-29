import hashlib
from pathlib import Path

from app.config import OS_JUNK_FILES, SKIP_DIRS


def _norm(data: bytes) -> bytes:
    if b"\x00" in data[:8192]:      # 바이너리 휴리스틱 — 원문 그대로
        return data
    return data.replace(b"\r\n", b"\n")


def tree_fingerprint(root: Path) -> str:
    entries = []
    for f in sorted(root.rglob("*")):
        if not f.is_file() or f.is_symlink():
            continue
        rel = f.relative_to(root)
        if set(rel.parts) & SKIP_DIRS or f.name in OS_JUNK_FILES:
            continue
        digest = hashlib.sha256(_norm(f.read_bytes())).hexdigest()
        entries.append(f"{rel.as_posix()}\0{digest}")
    return hashlib.sha256("\n".join(entries).encode()).hexdigest()
