#!/usr/bin/env python3
"""ansim-benchmark 저장소 전체 불변식 검사 — 명세 §1.3 (계획 Task 26 Step 3).

P8·P9·P10은 저장소 **전체**의 부재를 판정한다. 벤치마크 어딘가에 로깅 import 한 줄,
처리방침 파일명 하나, 삭제 동사 한 단어가 들어오면 그 양성이 조용히 사라진다.
문서로만 적어 두면 나중 수정에서 반드시 깨지므로 실행 가능한 검사로 강제한다.

이 스크립트가 벤치마크 저장소가 아니라 **안심코드 저장소**에 사는 이유가 여기 있다.
검사에 필요한 정규식 리터럴(`import logging`·`privacy`·삭제 동사)을 스스로 품어야 하는데,
벤치마크 안에 커밋하면 자기 소스가 P8·P9·P10을 전부 마스킹한다.

사용:
    python verification/check_invariants.py <benchmark_root>

위반이 있으면 목록을 출력하고 종료 코드 1로 끝난다.
"""

import argparse
import re
import sys
from pathlib import Path

# api/app/config.py·engine/repo_checks.py와 같은 값을 쓴다(스캔 대상 정의가 곧 검사 범위다).
SKIP_DIRS = {"node_modules", "venv", ".venv", ".git", "__pycache__", "__MACOSX", "dist", "build"}
CODE_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx"}

# 각 패턴은 api/app/engine의 대응 정규식과 1:1이다. 엔진이 바뀌면 여기도 같이 바꾼다.
LOGGING = re.compile(r"import logging|require\(['\"]winston['\"]\)|require\(['\"]pino['\"]\)|"
                     r"from ['\"]winston['\"]|from ['\"]pino['\"]")          # repo_checks.py:98 (P8)
PRIVACY_FILE = re.compile(r"(?i)privacy|개인정보처리방침")                     # repo_checks.py:104 (P9)
PRIVACY_ROUTE = re.compile(r"(?i)['\"]/?privacy")                            # repo_checks.py:104 (P9)
DELETION = re.compile(r"(?i)\b(delete|destroy|expire|retention|purge)\b|파기")  # repo_checks.py:64 (P10)
PII_FIELD = re.compile(r"(?i)phone|birth|email|address|jumin|rrn|이름|전화|주소")  # analysis.py:103 (P4)
EXTERNAL_SEND = re.compile(r"requests\.post|fetch\(|axios\.")                # analysis.py:104 (P4)
AUTH = re.compile(r"login_required|Depends\(|authenticate|passport|jwt_required|"
                  r"@auth|check_auth|requires_auth")                         # repo_checks.py:53 (P7)
PY_IMPORT = re.compile(r"^\s*(?:import\s+([A-Za-z_][\w.]*)|from\s+([A-Za-z_][\w.]*)\s+import)",
                       re.MULTILINE)
JS_IMPORT = re.compile(r"""require\(['"]([^'"]+)['"]\)|from\s+['"]([^'"]+)['"]""")

# 의도된 SCA-01 — 코드가 import 하지만 매니페스트에 일부러 선언하지 않은 것들.
INTENDED_UNDECLARED = {"redis", "left-pad"}

# P4 불변식(⑤)의 유일한 허용 파일 — 여기서만 PII 필드와 외부 전송이 함께 나온다.
P4_ALLOWED = "vulnerable/third_party.py"

# P7 불변식(⑥)의 적용 범위 — clean/admin_ok.py는 오히려 인증 단어가 있어야 음성이 된다.
P7_MUST_LACK_AUTH = ("vulnerable/admin_routes.py", "vulnerable/admin.js")
P7_MUST_HAVE_AUTH = ("clean/admin_ok.py",)

# import 이름 → 배포 패키지 이름. api/app/engine/repo_checks.py의 표와 같은 목적이다.
PY_IMPORT_TO_DIST = {
    "bs4": "beautifulsoup4", "PIL": "pillow", "yaml": "pyyaml", "cv2": "opencv-python",
    "sklearn": "scikit-learn", "dateutil": "python-dateutil", "jwt": "pyjwt",
    "attr": "attrs", "dotenv": "python-dotenv", "OpenSSL": "pyopenssl",
}
PY_STDLIB = set(sys.stdlib_module_names)


def canon(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        if set(path.relative_to(root).parts[:-1]) & SKIP_DIRS:
            continue
        yield path


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _declared_packages(root: Path) -> set[str]:
    """매니페스트에 선언된 패키지 이름 집합 — 파이썬·npm을 한 집합으로 합친다."""
    declared: set[str] = set()
    for path in _iter_files(root):
        name = path.name
        if re.fullmatch(r"requirements.*\.txt", name):
            for raw in _read(path).splitlines():
                line = raw.split("#", 1)[0].strip()
                if not line or line.startswith("-"):
                    continue
                pkg = re.split(r"[<>=!~\[; ]|@", line, maxsplit=1)[0].strip()
                if pkg:
                    declared.add(canon(pkg))
        elif name == "package.json":
            for match in re.finditer(r'"([^"]+)"\s*:\s*"[^"]*"', _read(path)):
                declared.add(canon(match.group(1)))
    return declared


def _imported_packages(root: Path) -> dict[str, list[str]]:
    """코드가 import 하는 비표준 패키지 → 등장 파일 목록."""
    imports: dict[str, list[str]] = {}
    for path in _iter_files(root):
        if path.suffix.lower() not in CODE_EXTS:
            continue
        rel = path.relative_to(root).as_posix()
        text = _read(path)
        if path.suffix.lower() == ".py":
            for match in PY_IMPORT.finditer(text):
                top = (match.group(1) or match.group(2)).split(".")[0]
                if top in PY_STDLIB or top.startswith("_"):
                    continue
                imports.setdefault(canon(PY_IMPORT_TO_DIST.get(top, top)), []).append(rel)
        else:
            for match in JS_IMPORT.finditer(text):
                mod = match.group(1) or match.group(2)
                if mod.startswith((".", "/")) or mod.startswith("node:"):
                    continue
                pkg = "/".join(mod.split("/")[:2]) if mod.startswith("@") else mod.split("/")[0]
                imports.setdefault(canon(pkg), []).append(rel)
    return imports


def check(root: Path) -> list[str]:
    """불변식 위반 목록. 비어 있으면 통과다."""
    violations: list[str] = []
    code_files = [p for p in _iter_files(root) if p.suffix.lower() in CODE_EXTS]

    # ① 로깅 라이브러리 부재 (P8)
    for path in code_files:
        if LOGGING.search(_read(path)):
            violations.append(f"① P8 마스킹: {path.relative_to(root)}에 로깅 라이브러리 반입")

    # ② 처리방침 파일명·라우트 부재 (P9)
    for path in _iter_files(root):          # 파일명은 비코드 파일까지 본다
        if PRIVACY_FILE.search(path.name):
            violations.append(f"② P9 마스킹: 처리방침으로 읽히는 파일명 {path.relative_to(root)}")
    for path in code_files:
        if PRIVACY_ROUTE.search(_read(path)):
            violations.append(f"② P9 마스킹: {path.relative_to(root)}에 /privacy 라우트")

    # ③ 삭제 동사 부재 (P10)
    for path in code_files:
        hit = DELETION.search(_read(path))
        if hit:
            violations.append(f"③ P10 마스킹: {path.relative_to(root)}에 삭제 동사 '{hit.group(0)}'")

    # ④ 비표준 import는 전부 선언 (의도된 SCA-01만 예외)
    declared = _declared_packages(root)
    for pkg, files in sorted(_imported_packages(root).items()):
        if pkg in declared or pkg in INTENDED_UNDECLARED:
            continue
        violations.append(f"④ 의도치 않은 SCA-01: `{pkg}` 미선언 ({', '.join(sorted(set(files)))})")

    # ⑤ PII 필드 + 외부 전송 호출 동시 등장은 third_party.py에서만 (P4)
    for path in code_files:
        rel = path.relative_to(root).as_posix()
        text = _read(path)
        if PII_FIELD.search(text) and EXTERNAL_SEND.search(text) and rel != P4_ALLOWED:
            violations.append(f"⑤ P4 오라클 외 발화: {rel}에 PII 필드와 외부 전송 호출이 동시 등장")

    # ⑥ 인증 단어 — vulnerable/ admin 파일에는 부재, clean/admin_ok.py에는 존재 (P7)
    for rel in P7_MUST_LACK_AUTH:
        path = root / rel
        if path.is_file() and AUTH.search(_read(path)):
            violations.append(f"⑥ P7 마스킹: {rel}에 인증 단어 등장")
        elif not path.is_file():
            violations.append(f"⑥ P7 케이스 소실: {rel}가 없다")
    for rel in P7_MUST_HAVE_AUTH:
        path = root / rel
        if not path.is_file():
            violations.append(f"⑥ P7 음성 케이스 소실: {rel}가 없다")
        elif not AUTH.search(_read(path)):
            violations.append(f"⑥ P7 음성 무효: {rel}에 인증 단어가 없어 오탐 케이스가 된다")

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="ansim-benchmark 저장소 불변식 검사 (명세 §1.3)")
    parser.add_argument("benchmark_root", type=Path, help="ansim-benchmark 체크아웃 경로")
    args = parser.parse_args()

    root = args.benchmark_root.resolve()
    if not root.is_dir():
        print(f"경로가 디렉토리가 아니다: {root}", file=sys.stderr)
        return 2

    violations = check(root)
    if violations:
        print(f"불변식 위반 {len(violations)}건 — 벤치마크 양성이 마스킹된다:\n", file=sys.stderr)
        for line in violations:
            print(f"  - {line}", file=sys.stderr)
        print("\n명세 docs/benchmark-spec.md §1.3 참조.", file=sys.stderr)
        return 1

    print(f"불변식 6종 통과 — {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
