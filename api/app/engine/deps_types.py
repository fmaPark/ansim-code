"""의존성 파서(Task 6·7)와 SBOM 빌더(Task 8)·SCA 룰(Task 11)이 공유하는 자료형."""

from dataclasses import dataclass


@dataclass
class Dependency:
    ecosystem: str                 # "pypi" | "npm"
    name: str
    version: str | None
    declared_in: str               # 선언 파일의 저장소 상대 경로 (또는 "vendor")
    is_pinned: bool                # 정확 버전 고정 여부 (SCA-11 입력)
    integrity: str | None          # lock 파일의 무결성 해시 (SBOM ⑦ · SCA-09 입력)
    relationship: str              # "direct" | "transitive" (SBOM ⑪)
    registry_source: bool          # 공개 레지스트리 출처 여부 (SCA-10 입력)
    vendored_path: str | None      # 저장소에 복제된 경우의 경로 (SBOM ⑨ 입력)


@dataclass
class ParseMarker:
    """파싱 불가·부재를 남기는 마커.

    G7(코드 실행 금지) 때문에 setup.py만 있는 저장소는 의존성을 알 수 없다.
    그 사실 자체가 SCA-09·11 판단 입력이므로 예외로 죽이지 않고 마커로 남긴다.
    """

    kind: str                      # 예: "python_manifest_unparsable" | "no_lockfile"
    detail: str
