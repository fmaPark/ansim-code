"""Python 의존성 선언 파서 — requirements / pyproject / lock 3계열.

G7(코드 실행 금지): `setup.py`는 절대 실행하지 않는다. setup.py만 있는 저장소는
"의존성 선언 파싱 불가" 마커를 남겨 SCA-09·11의 판단 입력으로 넘긴다.
"""

import re
from pathlib import Path

from pip_requirements_parser import RequirementsFile

from app.config import SKIP_DIRS
from app.engine.deps_types import Dependency, ParseMarker

try:                            # 프로젝트 타깃은 3.12지만 3.10 환경에서도 돌아야 한다
    import tomllib
except ModuleNotFoundError:     # Python < 3.11
    import tomli as tomllib     # type: ignore[no-redef]

_LOCK_FILES = ("poetry.lock", "uv.lock", "Pipfile.lock", "requirements.lock")
_EXACT_SPEC = re.compile(r"^==\s*[^,\s]+$")
_VCS_PREFIXES = ("git+", "hg+", "svn+", "bzr+", "file:", "http://", "https://")


def _iter_files(root: Path, pattern: str):
    for f in sorted(root.rglob(pattern)):
        if not f.is_file() or set(f.relative_to(root).parts) & SKIP_DIRS:
            continue
        yield f


def find_python_lockfiles(root: Path) -> list[str]:
    """SCA-11(버전 미고정 & lock 부재) 판정용 — 존재하는 lock 파일 상대 경로."""
    found = []
    for name in _LOCK_FILES:
        found += [str(f.relative_to(root).as_posix()) for f in _iter_files(root, name)]
    return sorted(found)


def _canon(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _from_requirements(root: Path) -> list[Dependency]:
    deps: list[Dependency] = []
    for f in _iter_files(root, "requirements*.txt"):
        try:
            rf = RequirementsFile.from_file(str(f), include_nested=True)
        except Exception:
            continue                     # 깨진 선언 파일 하나가 스캔을 죽이지 않는다
        rel = f.relative_to(root).as_posix()
        for req in rf.requirements:
            if not req.name:
                continue                 # `-e ./local` 처럼 이름 없는 항목
            pinned = bool(req.is_pinned)
            version = req.get_pinned_version if pinned else None
            registry = not (req.is_editable or req.is_vcs_url or req.is_url or bool(req.link))
            deps.append(Dependency(
                ecosystem="pypi", name=req.name, version=version, declared_in=rel,
                is_pinned=pinned, integrity=(req.hash_options or [None])[0],
                relationship="direct", registry_source=registry, vendored_path=None))
    return deps


def _spec_version(spec: str | None) -> tuple[str | None, bool]:
    """PEP 508 스펙 문자열 → (고정 버전, 고정 여부)."""
    if not spec:
        return None, False
    spec = spec.strip()
    if _EXACT_SPEC.match(spec):
        return spec[2:].strip(), True
    if re.fullmatch(r"[0-9][\w.\-+]*", spec):     # poetry의 `"2.0.1"` 형태
        return spec, True
    return None, False


def _from_pyproject(root: Path) -> list[Dependency]:
    deps: list[Dependency] = []
    for f in _iter_files(root, "pyproject.toml"):
        try:
            data = tomllib.loads(f.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        rel = f.relative_to(root).as_posix()

        for raw in (data.get("project") or {}).get("dependencies") or []:
            m = re.match(r"^\s*([A-Za-z0-9._-]+)", str(raw))
            if not m:
                continue
            name = m.group(1)
            rest = str(raw)[m.end():].strip()
            at_url = rest.startswith("@")
            version, pinned = _spec_version(rest.split(";")[0] if not at_url else None)
            deps.append(Dependency(
                ecosystem="pypi", name=name, version=version, declared_in=rel,
                is_pinned=pinned, integrity=None, relationship="direct",
                registry_source=not at_url, vendored_path=None))

        poetry = ((data.get("tool") or {}).get("poetry") or {}).get("dependencies") or {}
        for name, constraint in poetry.items():
            if name.lower() == "python":
                continue
            registry = True
            if isinstance(constraint, dict):
                registry = not any(k in constraint for k in ("git", "path", "url"))
                constraint = constraint.get("version")
            version, pinned = _spec_version(constraint if isinstance(constraint, str) else None)
            deps.append(Dependency(
                ecosystem="pypi", name=name, version=version, declared_in=rel,
                is_pinned=pinned, integrity=None, relationship="direct",
                registry_source=registry, vendored_path=None))
    return deps


def _from_locks(root: Path) -> list[Dependency]:
    """poetry.lock·uv.lock의 `[[package]]` 항목 — 파싱만 하고 실행하지 않는다."""
    deps: list[Dependency] = []
    for name in ("poetry.lock", "uv.lock"):
        for f in _iter_files(root, name):
            try:
                data = tomllib.loads(f.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            rel = f.relative_to(root).as_posix()
            for pkg in data.get("package") or []:
                pkg_name = pkg.get("name")
                if not pkg_name:
                    continue
                integrity = None
                files = pkg.get("files") or []
                if isinstance(files, list) and files and isinstance(files[0], dict):
                    integrity = files[0].get("hash")
                wheels = pkg.get("wheels") or []
                if integrity is None and isinstance(wheels, list) and wheels and isinstance(wheels[0], dict):
                    integrity = wheels[0].get("hash")
                source = pkg.get("source") or {}
                registry = not (isinstance(source, dict) and source.get("type") in {"git", "directory", "path", "url"})
                deps.append(Dependency(
                    ecosystem="pypi", name=pkg_name, version=pkg.get("version"), declared_in=rel,
                    is_pinned=bool(pkg.get("version")), integrity=integrity,
                    relationship="transitive", registry_source=registry, vendored_path=None,
                    in_lock=True))
    return deps


def python_parse_markers(root: Path) -> list[ParseMarker]:
    """G7 때문에 해석할 수 없는 선언 형태를 마커로 남긴다."""
    markers: list[ParseMarker] = []
    has_declaration = any(_iter_files(root, "requirements*.txt")) or any(_iter_files(root, "pyproject.toml"))
    setup_py = list(_iter_files(root, "setup.py"))
    if setup_py and not has_declaration:
        markers.append(ParseMarker(
            kind="python_manifest_unparsable",
            detail=f"{setup_py[0].relative_to(root).as_posix()}만 존재 — 코드 실행 금지(G7)로 의존성 선언 파싱 불가"))
    return markers


def parse_python_deps(root: Path) -> list[Dependency]:
    """선언(direct)을 기준으로 lock 항목(transitive)을 병합한 목록."""
    direct = _from_requirements(root) + _from_pyproject(root)
    merged: dict[str, Dependency] = {}
    for d in direct:
        merged.setdefault(_canon(d.name), d)

    for locked in _from_locks(root):
        key = _canon(locked.name)
        existing = merged.get(key)
        if existing is None:
            merged[key] = locked
            continue
        # lock이 있으면 direct의 실제 설치 버전·무결성 해시를 lock에서 채운다.
        if locked.version:
            existing.version = locked.version
            existing.is_pinned = True
        if existing.integrity is None:
            existing.integrity = locked.integrity
        existing.in_lock = True
    return list(merged.values())
