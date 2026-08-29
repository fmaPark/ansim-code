"""Python import 추출 — stdlib `ast`만 사용한다(G7: 코드 실행 금지)."""

import ast
import sys
from pathlib import Path

from app.config import SKIP_DIRS


def extract_python_imports(root: Path) -> set[str]:
    """저장소의 최상위 import 이름 집합 — stdlib·로컬 모듈·상대 import는 제외한다.

    SCA-01(미선언 의존성)의 좌변이다: 이 집합 − 매니페스트 선언 = 갭.
    """
    found: set[str] = set()
    for f in root.rglob("*.py"):
        if set(f.relative_to(root).parts) & SKIP_DIRS:
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, ValueError, OSError):
            continue          # 문법 오류 파일은 건너뛴다 — 전체 스캔을 죽이지 않는다
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
    local = {p.stem for p in root.iterdir()} | {p.name for p in root.iterdir() if p.is_dir()}
    return {m for m in found if m not in sys.stdlib_module_names and m not in local}
