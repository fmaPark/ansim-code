import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Scan(Base):
    __tablename__ = "scans"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    source_type: Mapped[str] = mapped_column(String(8))            # git|zip
    source_ref: Mapped[str] = mapped_column(Text)                  # URL 또는 업로드 파일명
    previous_scan_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("scans.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(8), default="queued")   # queued|running|done|failed
    current_stage: Mapped[str | None] = mapped_column(String(16))  # 환경분석|현황진단|위험분석|대책수립|완료
    error_message: Mapped[str | None] = mapped_column(Text)
    supply_chain_class: Mapped[str | None] = mapped_column(String(16))  # 자체개발|오픈소스|바이너리
    grade: Mapped[str | None] = mapped_column(String(4))           # 안심|주의|위험
    content_fingerprint: Mapped[str | None] = mapped_column(String(80))
    fingerprint_type: Mapped[str | None] = mapped_column(String(16))    # git_commit|tree_hash
    rule_catalog_version: Mapped[str | None] = mapped_column(String(64))
    llm_model_id: Mapped[str | None] = mapped_column(String(64))   # API 응답 model 그대로 (G9)
    vuln_db_snapshot_date: Mapped[str | None] = mapped_column(String(64))  # "OSV@...; KISA-CSV@..."
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    public_slug: Mapped[str | None] = mapped_column(String(16), unique=True)
    publish_token: Mapped[str | None] = mapped_column(String(64))
    report_json: Mapped[dict | None] = mapped_column(JSONB)        # 개발자용 리포트 (Task 19)
    easy_report_json: Mapped[dict | None] = mapped_column(JSONB)   # 시민용
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    purged_at: Mapped[datetime | None] = mapped_column(DateTime)


class SbomComponent(Base):                     # 0309 §5.2 15속성 1:1 (TDD §4.3)
    __tablename__ = "sbom_components"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scans.id"))
    validation_tool: Mapped[str] = mapped_column(String(64), default="AnsimCode")  # ①
    supplier: Mapped[str | None] = mapped_column(String(128))      # ②
    author: Mapped[str | None] = mapped_column(String(128))        # ③
    component_name: Mapped[str] = mapped_column(String(214))       # ④
    version: Mapped[str | None] = mapped_column(String(64))        # ⑤
    unique_id: Mapped[str] = mapped_column(Text)                   # ⑥ purl
    component_hash: Mapped[str | None] = mapped_column(Text)       # ⑦ lock integrity
    license_name: Mapped[str | None] = mapped_column(String(128))  # ⑧
    license_usage: Mapped[str | None] = mapped_column(String(16))  # ⑨ 동적참조|파일단위복제|복제·고지없음
    vulnerability_db: Mapped[list | None] = mapped_column(JSONB)   # ⑩ 취약점별 출처 [{id,source}]
    relationship: Mapped[str | None] = mapped_column(String(32))   # ⑪ direct|transitive
    release_date: Mapped[str | None] = mapped_column(String(32))   # ⑫
    cve_ids: Mapped[list | None] = mapped_column(JSONB)            # ⑬
    cvss_base: Mapped[float | None] = mapped_column()              # ⑭ §6.14 3값
    cvss_impact: Mapped[float | None] = mapped_column()
    cvss_exploitability: Mapped[float | None] = mapped_column()
    cvss_null_reason: Mapped[str | None] = mapped_column(String(64))  # 벡터 부재 시 사유
    cvss_severity: Mapped[str | None] = mapped_column(String(8))   # ⑮ critical|high|medium|low
    ecosystem: Mapped[str] = mapped_column(String(8))              # pypi|npm (내부용)


class Finding(Base):
    __tablename__ = "findings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scans.id"))
    rule_id: Mapped[str] = mapped_column(String(16))
    severity: Mapped[str] = mapped_column(String(8))
    file_path: Mapped[str | None] = mapped_column(Text)
    line: Mapped[int | None] = mapped_column(Integer)
    evidence: Mapped[str | None] = mapped_column(Text)             # 항상 마스킹본 (G2)
    status: Mapped[str] = mapped_column(String(16))                # confirmed|review_needed
    grade_blocking: Mapped[bool] = mapped_column(Boolean, default=False)
    judge_explanation: Mapped[str | None] = mapped_column(Text)    # LLM 판정 설명(참고용)
    judge_evidence_lines: Mapped[list | None] = mapped_column(JSONB)
    fix_prompt: Mapped[str | None] = mapped_column(Text)
    easy_description: Mapped[str | None] = mapped_column(Text)


class Rule(Base):
    __tablename__ = "rules"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)  # SCA-01…P10…AUX-04
    standard_ref: Mapped[str] = mapped_column(String(64))          # 예: TTAK.KO-12.0414 §7.3.4
    secondary_ref: Mapped[str | None] = mapped_column(String(128)) # 보조 룰 2차 출처
    title: Mapped[str] = mapped_column(String(128))
    # sca|static|llm|static+llm — TDD §4.3은 3종이나 §4.5 방식 컬럼이 P2·P3·P5·P10에
    # `static + LLM`을 요구해 4번째 값이 실재한다. String(8)이면 시드 시 절단 오류.
    type: Mapped[str] = mapped_column(String(16))
    severity_default: Mapped[str] = mapped_column(String(16))      # critical|high|medium|low|cvss_derived
    derivation: Mapped[str] = mapped_column(String(8))             # direct|aux (§4.5 구분 표기)
