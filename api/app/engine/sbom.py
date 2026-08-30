"""SBOM 빌더 — 0309 §5.2 15속성 + §6.9 결합형태 3분류 + 0322 §5.1.1 공급망 분류.

이 모듈 자체는 레지스트리 원격 조회를 하지 않는다(매니페스트·lock·동봉 LICENSE에서
얻는 범위만). 원격 보강은 `registry.py`의 파이프라인 단계가 수행한다(이슈 #33).
부족한 속성은 null로 두되 **15속성 키는 언제나 전부 출력**한다.
"""

import json
import re
from pathlib import Path

from packageurl import PackageURL

from app.config import SKIP_DIRS
from app.engine.deps_types import Dependency

VENDOR_DIRS = ("vendor", "vendors", "third_party", "thirdparty", "libs")
LICENSE_FILES = ("LICENSE", "LICENCE", "COPYING", "NOTICE")
BINARY_SUFFIXES = {".so", ".dll", ".jar", ".exe", ".dylib", ".a", ".class", ".war", ".pyd"}

# 결합 형태 3분류 (TDD §4.3 ⑨ · 0309 §6.9). "수정 후 사용" 해시 대조는 V2 — 구현하지 않는다.
USAGE_DYNAMIC = "동적 참조"
USAGE_FILE_COPY = "파일단위 복제"
USAGE_NO_NOTICE = "복제·고지 없음"

# SPDX 식별자 후보 — 동봉 LICENSE 본문과 레지스트리 응답 문자열이 공유하는 패턴.
_LICENSE_PATTERNS = [
    # AFFERO 한 단어로 잡는다 — PyPI 원문에 "GNU AFFERO GPL 3.0"처럼 줄여 쓴 표기가 있어
    # 전체 문구만 요구하면 아래 GPL 패턴이 먼저 삼킨다(PyMuPDF 실측).
    (re.compile(r"\bAFFERO\b|\bAGPL[- ]?3", re.I), "AGPL-3.0"),
    (re.compile(r"\bServer Side Public License\b|\bSSPL\b", re.I), "SSPL-1.0"),
    (re.compile(r"\bGNU LESSER GENERAL PUBLIC LICENSE\b|\bLGPL\b", re.I), "LGPL-3.0"),
    (re.compile(r"\bGNU GENERAL PUBLIC LICENSE\b|\bGPL[- ]?3", re.I), "GPL-3.0"),
    (re.compile(r"\bApache License\b|\bApache-2\.0\b", re.I), "Apache-2.0"),
    (re.compile(r"\bMIT License\b|\bThe MIT\b", re.I), "MIT"),
    (re.compile(r"\bBSD\b", re.I), "BSD-3-Clause"),
    (re.compile(r"\bMozilla Public License\b|\bMPL[- ]?2", re.I), "MPL-2.0"),
    (re.compile(r"\bISC License\b", re.I), "ISC"),
]


def normalize_license(raw: str | None) -> str | None:
    """원문 라이선스 문자열 → SPDX id(패턴 일치 시) 또는 짧은 토큰 보존.

    PyPI `info.license`가 라이선스 전문 수천 자인 패키지가 있다 — 컬럼(String(128))
    보호를 위해 패턴 불일치 장문은 None으로 버리고 호출자가 다음 후보로 폴스루한다.
    `"(MIT OR AGPL-3.0)"` 같은 SPDX 식 토큰은 원문 그대로 남긴다(_is_service_copyleft가
    부분 문자열로 매칭한다).
    """
    text = (raw or "").strip()
    if not text:
        return None
    for pattern, spdx in _LICENSE_PATTERNS:
        if pattern.search(text):
            return spdx
    if "\n" not in text and len(text) <= 64:
        return text
    return None


_SUPPLIER = {"pypi": "PyPI", "npm": "npm registry"}

# 0309 §5.2 15속성 — SBOM 응답·룰 입력이 공유하는 키 순서.
SBOM_ATTRIBUTE_KEYS = (
    "validation_tool", "supplier", "author", "component_name", "version", "unique_id",
    "component_hash", "license_name", "license_usage", "vulnerability_db", "relationship",
    "release_date", "cve_ids", "cvss_base", "cvss_severity",
)
# 15속성 밖의 보조 필드 — §6.14 3값 중 나머지·null 사유·내부 생태계 구분.
SBOM_EXTRA_KEYS = ("cvss_impact", "cvss_exploitability", "cvss_null_reason", "ecosystem")


def component_row(component) -> dict:
    """SbomComponent → 룰 러너·API가 쓰는 dict(컬럼명 그대로)."""
    return {k: getattr(component, k) for k in SBOM_ATTRIBUTE_KEYS + SBOM_EXTRA_KEYS}


def _rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def detect_vendored(root: Path) -> dict[str, bool]:
    """vendor 계열 디렉토리 하위 1단계 → {상대경로: LICENSE·COPYING 존재 여부} (SCA-06 입력)."""
    found: dict[str, bool] = {}
    for base in sorted(root.rglob("*")):
        # 저장소 루트가 아니라 하위 경로에 vendor/가 있는 배치(zip 안 프로젝트 폴더 등)도 잡는다.
        if not base.is_dir() or base.name not in VENDOR_DIRS:
            continue
        if set(base.relative_to(root).parts) & SKIP_DIRS:
            continue
        for child in sorted(base.iterdir()):
            if not child.is_dir() or child.name in SKIP_DIRS:
                continue
            found[_rel(root, child)] = _has_license_file(child)
    return found


def _has_license_file(directory: Path) -> bool:
    for f in directory.iterdir():
        if not f.is_file():
            continue
        stem = f.name.split(".")[0].upper()
        if stem in LICENSE_FILES:
            return True
    return False


def _license_from_dir(directory: Path) -> str | None:
    """동봉 LICENSE 본문·package.json의 license 필드에서 얻는 범위만."""
    pkg = directory / "package.json"
    if pkg.is_file():
        try:
            meta = json.loads(pkg.read_text(encoding="utf-8", errors="ignore"))
            lic = meta.get("license")
            if isinstance(lic, str) and lic:
                return lic[:128]
            if isinstance(lic, dict) and lic.get("type"):
                return str(lic["type"])[:128]
        except (json.JSONDecodeError, OSError):
            pass
    for f in sorted(directory.iterdir()):
        if not f.is_file() or f.name.split(".")[0].upper() not in LICENSE_FILES:
            continue
        try:
            head = f.read_text(encoding="utf-8", errors="ignore")[:4000]
        except OSError:
            continue
        for pattern, spdx in _LICENSE_PATTERNS:
            if pattern.search(head):
                return spdx
    return None


def _purl(dep: Dependency) -> str:
    namespace, name = None, dep.name
    if dep.ecosystem == "npm" and name.startswith("@") and "/" in name:
        namespace, name = name.split("/", 1)
    return PackageURL(type=dep.ecosystem, namespace=namespace,
                      name=name, version=dep.version or None).to_string()


def _author_from_dir(directory: Path) -> str | None:
    pkg = directory / "package.json"
    if not pkg.is_file():
        return None
    try:
        meta = json.loads(pkg.read_text(encoding="utf-8", errors="ignore"))
    except (json.JSONDecodeError, OSError):
        return None
    author = meta.get("author")
    if isinstance(author, str):
        return author[:128] or None
    if isinstance(author, dict) and author.get("name"):
        return str(author["name"])[:128]
    return None


def build_sbom(deps: list[Dependency], root: Path) -> list[dict]:
    """15속성 dict 목록 — 키 이름은 SbomComponent 컬럼과 1:1이다."""
    root = Path(root)
    vendored = detect_vendored(root)
    rows: list[dict] = []
    for dep in deps:
        license_name: str | None = None
        author: str | None = None
        if dep.vendored_path:
            has_license = vendored.get(dep.vendored_path)
            vdir = root / dep.vendored_path
            if has_license is None and vdir.is_dir():
                has_license = _has_license_file(vdir)
            usage = USAGE_FILE_COPY if has_license else USAGE_NO_NOTICE
            if vdir.is_dir():
                license_name = _license_from_dir(vdir)
                author = _author_from_dir(vdir)
        else:
            usage = USAGE_DYNAMIC

        rows.append({
            "validation_tool": "AnsimCode",                                   # ①
            "supplier": _SUPPLIER.get(dep.ecosystem) if dep.registry_source else None,   # ②
            "author": author,                                                 # ③
            "component_name": dep.name,                                       # ④
            "version": dep.version,                                           # ⑤
            "unique_id": _purl(dep),                                          # ⑥
            "component_hash": dep.integrity,                                  # ⑦ lock integrity
            "license_name": license_name,                                     # ⑧
            "license_usage": usage,                                           # ⑨
            "vulnerability_db": None,                                         # ⑩ Task 9·10이 채운다
            "relationship": dep.relationship,                                 # ⑪
            "release_date": None,                                             # ⑫ stage_registry가 채운다
            "cve_ids": None,                                                  # ⑬ Task 9
            "cvss_base": None,                                                # ⑭ Task 9
            "cvss_impact": None,
            "cvss_exploitability": None,
            "cvss_null_reason": None,
            "cvss_severity": None,                                            # ⑮ Task 9
            "ecosystem": dep.ecosystem,                                       # 내부용
        })
    return rows


def _has_binary(root: Path) -> bool:
    for f in root.rglob("*"):
        if not f.is_file() or f.is_symlink():
            continue
        if set(f.relative_to(root).parts) & SKIP_DIRS:
            continue
        if f.suffix.lower() in BINARY_SUFFIXES:
            return True
    return False


def classify_supply_chain(deps: list[Dependency], root: Path) -> str:
    """0322 §5.1.1 공급망 환경 분류 — 자체개발 | 오픈소스 | 바이너리."""
    root = Path(root)
    if _has_binary(root):
        return "바이너리"          # 동봉 바이너리는 검증 불가 구간이라 우선 분류한다
    if not deps:
        return "자체개발"
    return "오픈소스"


def vendored_dependencies(root: Path, declared: list[Dependency]) -> list[Dependency]:
    """vendor 디렉토리에만 존재하는 컴포넌트를 Dependency로 승격한다 (SCA-06 입력)."""
    root = Path(root)
    known = {d.name.lower() for d in declared}
    extra: list[Dependency] = []
    for path, _has_license in detect_vendored(root).items():
        name = path.rsplit("/", 1)[-1]
        if name.lower() in known:
            continue
        vdir = root / path
        exts = {f.suffix.lower() for f in vdir.rglob("*") if f.is_file()}
        ecosystem = "npm" if (exts & {".js", ".ts", ".mjs", ".cjs"} or (vdir / "package.json").is_file()) else "pypi"
        extra.append(Dependency(
            ecosystem=ecosystem, name=name, version=None,
            declared_in=path.rsplit("/", 1)[0] or path,      # 예: app/vendor
            is_pinned=False, integrity=None, relationship="direct",
            registry_source=False, vendored_path=path))
    return extra
