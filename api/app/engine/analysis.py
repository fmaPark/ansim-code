"""위험분석 스테이지 오케스트레이션 (Task 14~16).

pipeline.py의 변경을 최소화하기 위해(M2·M3 병렬 세션과의 충돌 회피) 정적 룰
실행·마스킹·LLM 후보 선별을 이 모듈로 모았다. pipeline은 위험분석 단계에서
run_static_stage() 한 번 + (Task 16) judge 한 번만 호출한다.
"""
import logging
from pathlib import Path

from app.engine.findings import FindingDraft
from app.engine.gitleaks_runner import run_gitleaks
from app.engine.masking import MaskRegistry
from app.engine.pii import classify_secret

log = logging.getLogger(__name__)

# G2·G3: LLM 경유 대상 룰 — SEC-*는 원천 제외, confirmed 룰은 LLM 불필요.
LLM_RULES = {"P1", "P2", "P3", "P4", "P5", "P10"}


def run_static_stage(root: Path) -> tuple[list[FindingDraft], MaskRegistry]:
    """정적 룰 전체 실행 + 저장 마스킹(P0-2 ①패스).

    Task 14 시점: gitleaks(SEC-01~05) + 주민번호 체크섬 분기.
    Task 15에서 semgrep(P·AUX) + repo_checks(P7~P9)가 여기에 합류한다.
    """
    registry = MaskRegistry()
    drafts: list[FindingDraft] = []

    # ── 시크릿 룰 (Task 12·13) ──
    for raw in run_gitleaks(root):
        registry.add(raw.secret_value)
        d = classify_secret(raw)
        d.evidence = registry.mask(raw.match)   # 저장 직전 마스킹 (G2 ①)
        drafts.append(d)

    # 모든 draft의 evidence를 레지스트리 전체로 재마스킹 — 서로 다른 룰이 잡은
    # 같은 원문이 다른 finding의 evidence에 남는 경우까지 봉쇄한다.
    for d in drafts:
        if d.evidence:
            d.evidence = registry.mask(d.evidence)

    log.info("static stage done", extra={"findings": len(drafts), "secrets": len(registry)})
    return drafts, registry


def llm_candidates(drafts: list[FindingDraft]) -> list[FindingDraft]:
    """LLM judge 대상 선별 — SEC-* 원천 제외(G2), P계열 review_needed만."""
    return [d for d in drafts
            if not d.rule_id.startswith("SEC-") and d.rule_id in LLM_RULES]
