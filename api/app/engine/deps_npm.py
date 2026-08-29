"""npm 의존성 선언 파서 — package.json + package-lock.json(v1/v2/v3).

JS/TS의 import 추출은 여기서 하지 않는다 — Semgrep 패턴이 담당한다(Task 11, TDD §4.5).
"""

import json
import re
from pathlib import Path

from app.config import SKIP_DIRS
from app.engine.deps_types import Dependency

_NON_REGISTRY_PREFIXES = ("git+", "git:", "github:", "file:", "link:", "http://", "https://",
                          "portal:", "workspace:")
_EXACT_VERSION = re.compile(r"^\d+\.\d+\.\d+[\w.\-+]*$")
_LOCK_FILES = ("package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml")


def _iter_files(root: Path, pattern: str):
    for f in sorted(root.rglob(pattern)):
        if not f.is_file() or set(f.relative_to(root).parts) & SKIP_DIRS:
            continue
        yield f


def find_npm_lockfiles(root: Path) -> list[str]:
    """SCA-11(버전 미고정 & lock 부재) 판정용."""
    found = []
    for name in _LOCK_FILES:
        found += [f.relative_to(root).as_posix() for f in _iter_files(root, name)]
    return sorted(found)


def _is_registry(spec: str) -> bool:
    return not str(spec).startswith(_NON_REGISTRY_PREFIXES)


def _lock_entries(lock: dict) -> dict[str, dict]:
    """lock 파일 → {패키지 이름: 항목}. v2/v3의 `packages`를 우선 본다."""
    entries: dict[str, dict] = {}
    packages = lock.get("packages")
    if isinstance(packages, dict):
        for key, meta in packages.items():
            if not key or not isinstance(meta, dict):
                continue                      # "" 키는 루트 프로젝트 자신이다
            name = key.split("node_modules/")[-1]
            if name:
                entries.setdefault(name, meta)
    if not entries and isinstance(lock.get("dependencies"), dict):   # lockfileVersion 1
        def walk(node: dict):
            for name, meta in node.items():
                if isinstance(meta, dict):
                    entries.setdefault(name, meta)
                    if isinstance(meta.get("dependencies"), dict):
                        walk(meta["dependencies"])
        walk(lock["dependencies"])
    return entries


def parse_npm_deps(root: Path) -> list[Dependency]:
    deps: dict[str, Dependency] = {}

    for pkg_file in _iter_files(root, "package.json"):
        rel = pkg_file.relative_to(root).as_posix()
        try:
            manifest = json.loads(pkg_file.read_text(encoding="utf-8", errors="ignore"))
        except (json.JSONDecodeError, OSError):
            continue                       # 깨진 package.json 하나가 스캔을 죽이지 않는다
        if not isinstance(manifest, dict):
            continue

        declared: dict[str, str] = {}
        for field in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
            block = manifest.get(field)
            if isinstance(block, dict):
                declared.update({k: str(v) for k, v in block.items()})

        for name, spec in declared.items():
            deps[name] = Dependency(
                ecosystem="npm", name=name,
                version=spec if _EXACT_VERSION.match(spec) else None,
                declared_in=rel, is_pinned=bool(_EXACT_VERSION.match(spec)),
                integrity=None, relationship="direct",
                registry_source=_is_registry(spec), vendored_path=None)

        # 같은 디렉토리의 lock을 병합한다 — 선언에 있으면 direct 유지, 없으면 transitive.
        lock_file = pkg_file.with_name("package-lock.json")
        if not lock_file.is_file():
            lock_file = pkg_file.with_name("npm-shrinkwrap.json")
        if not lock_file.is_file():
            continue
        try:
            lock = json.loads(lock_file.read_text(encoding="utf-8", errors="ignore"))
        except (json.JSONDecodeError, OSError):
            continue
        lock_rel = lock_file.relative_to(root).as_posix()
        for name, meta in _lock_entries(lock).items():
            resolved = str(meta.get("resolved") or "")
            existing = deps.get(name)
            if existing is not None:
                if meta.get("version"):
                    existing.version = str(meta["version"])
                    existing.is_pinned = True
                existing.integrity = meta.get("integrity") or existing.integrity
                if resolved and not _is_registry(resolved):
                    existing.registry_source = False
            else:
                deps[name] = Dependency(
                    ecosystem="npm", name=name,
                    version=str(meta["version"]) if meta.get("version") else None,
                    declared_in=lock_rel, is_pinned=bool(meta.get("version")),
                    integrity=meta.get("integrity"), relationship="transitive",
                    registry_source=_is_registry(resolved) if resolved else True,
                    vendored_path=None)

    return list(deps.values())
