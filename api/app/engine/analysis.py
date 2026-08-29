"""위험분석 스테이지 오케스트레이션 (Task 14~16).

pipeline.py의 변경을 최소화하기 위해(M2·M3 병렬 세션과의 충돌 회피) 정적 룰
실행·마스킹·LLM 후보 선별을 이 모듈로 모았다. pipeline은 위험분석 단계에서
run_static_stage() 한 번 + (Task 16) judge 한 번만 호출한다.
"""
import logging
from functools import lru_cache
from pathlib import Path

from app.engine.catalog import load_rules
from app.engine.findings import FindingDraft
from app.engine.gitleaks_runner import run_gitleaks
from app.engine.masking import MaskRegistry
from app.engine.pii import classify_secret
from app.engine.repo_checks import run_repo_checks
from app.engine.semgrep_runner import SemgrepHit, run_semgrep

log = logging.getLogger(__name__)

# G2·G3: LLM 경유 대상 룰 — SEC-*는 원천 제외, confirmed 룰은 LLM 불필요.
LLM_RULES = {"P1", "P2", "P3", "P4", "P5", "P10"}


@lru_cache(maxsize=1)
def _catalog() -> dict[str, dict]:
    return {r["id"]: r for r in load_rules()}


def drafts_from_semgrep(hits: list[SemgrepHit]) -> list[FindingDraft]:
    """SemgrepHit → FindingDraft. severity·status는 카탈로그(단일 사양)를 따른다(G3)."""
    drafts = []
    for h in hits:
        rule = _catalog().get(h.ansim_rule)
        if rule is None:
            continue
        status = "confirmed" if rule["verdict"] == "confirmed" else "review_needed"
        drafts.append(FindingDraft(
            rule_id=h.ansim_rule,
            severity=rule["severity_default"],
            file_path=h.file,
            line=h.line or None,
            evidence=h.evidence.strip()[:500],   # 저장 전 registry.mask()가 재마스킹
            status=status,
        ))
    return drafts


def run_static_stage(root: Path) -> tuple[list[FindingDraft], MaskRegistry]:
    """정적 룰 전체 실행 + 저장 마스킹(P0-2 ①패스).

    gitleaks(SEC-01~05, Task 12·13) + semgrep(P2·P3·P6·AUX, Task 15)
    + repo_checks(P5·P7~P10, Task 15). P1·P4는 static 트리거 없음 — LLM 단계 합성(Task 16).
    """
    registry = MaskRegistry()
    drafts: list[FindingDraft] = []

    # ── 시크릿 룰 (Task 12·13) ──
    for raw in run_gitleaks(root):
        registry.add(raw.secret_value)
        d = classify_secret(raw)
        d.evidence = registry.mask(raw.match)   # 저장 직전 마스킹 (G2 ①)
        drafts.append(d)

    # ── semgrep 룰 (Task 15: P2·P3·P6·AUX-01~04) ──
    drafts.extend(drafts_from_semgrep(run_semgrep(root)))

    # ── repo 단위 검사 (Task 15: P5·P7·P8·P9·P10) ──
    drafts.extend(run_repo_checks(root))

    # 모든 draft의 evidence를 레지스트리 전체로 재마스킹 — 서로 다른 룰이 잡은
    # 같은 원문이 다른 finding의 evidence에 남는 경우까지 봉쇄한다.
    for d in drafts:
        if d.evidence:
            d.evidence = registry.mask(d.evidence)

    log.info("static stage done", extra={"findings": len(drafts), "secrets": len(registry)})
    return drafts, registry


def persist_findings(db, scan_id, drafts: list[FindingDraft]) -> None:
    """FindingDraft → Finding insert (evidence는 이미 마스킹본 — G2)."""
    from app.models import Finding   # pipeline 경유 시에만 필요 — 순환·DB 의존 국소화

    for d in drafts:
        db.add(Finding(scan_id=scan_id, rule_id=d.rule_id, severity=d.severity,
                       file_path=d.file_path, line=d.line, evidence=d.evidence,
                       status=d.status, grade_blocking=d.grade_blocking,
                       judge_explanation=d.judge_explanation,
                       judge_evidence_lines=d.judge_evidence_lines))
    db.commit()


def llm_candidates(drafts: list[FindingDraft]) -> list[FindingDraft]:
    """LLM judge 대상 선별 — SEC-* 원천 제외(G2), P계열 review_needed만."""
    return [d for d in drafts
            if not d.rule_id.startswith("SEC-") and d.rule_id in LLM_RULES]
