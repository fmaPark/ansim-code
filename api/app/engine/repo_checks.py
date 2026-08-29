"""저장소 단위 검사. 이 태스크에서는 SCA-01(미선언 의존성)만 담당한다.

P7·P8·P9는 M4 트랙(Task 15)에서 같은 모듈에 추가된다.
"""

import re

from app.engine.deps_types import Dependency

# import 이름 ≠ 배포 패키지 이름인 대표 사례. 목록에 없는 이름은 정규화 후 그대로 비교한다.
PY_IMPORT_TO_DIST = {
    "PIL": "pillow", "yaml": "pyyaml", "bs4": "beautifulsoup4", "cv2": "opencv-python",
    "sklearn": "scikit-learn", "dateutil": "python-dateutil", "dotenv": "python-dotenv",
    "jwt": "pyjwt", "attr": "attrs", "OpenSSL": "pyopenssl", "serial": "pyserial",
    "Crypto": "pycryptodome", "MySQLdb": "mysqlclient", "psycopg2": "psycopg2-binary",
    "google": "google-api-python-client", "jose": "python-jose", "magic": "python-magic",
    "pkg_resources": "setuptools", "setuptools": "setuptools", "docx": "python-docx",
    "fitz": "pymupdf", "zoneinfo": "backports.zoneinfo",
}


def canon(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).strip().lower()


def undeclared_dependencies(deps: list[Dependency], imports_py: set[str],
                            imports_js: set[str]) -> list[tuple[str, str]]:
    """코드 import − 매니페스트 선언 = 갭 (SCA-01). → [(모듈명, 생태계)]"""
    declared_py = {canon(d.name) for d in deps if d.ecosystem == "pypi"}
    declared_js = {canon(d.name) for d in deps if d.ecosystem == "npm"}

    gaps: list[tuple[str, str]] = []
    for module in sorted(imports_py):
        candidates = {canon(module), canon(PY_IMPORT_TO_DIST.get(module, module))}
        if not candidates & declared_py:
            gaps.append((module, "pypi"))
    for module in sorted(imports_js):
        if canon(module) not in declared_js:
            gaps.append((module, "npm"))
    return gaps
