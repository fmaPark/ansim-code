"""FindingDraft — 룰 러너(gitleaks·pii·semgrep·repo_checks)가 생산하고
파이프라인이 Finding 행으로 저장하는 중간 표현 (Task 13~16 공용).

evidence는 이 시점부터 항상 마스킹본이어야 한다(G2).
status는 G3 등급 결정론의 입력 — LLM 단계(judge)는 절대 변경하지 않는다.
"""
from dataclasses import dataclass, field


@dataclass
class FindingDraft:
    rule_id: str
    severity: str
    file_path: str | None
    line: int | None
    evidence: str | None              # 항상 마스킹본 (G2)
    status: str                       # confirmed | review_needed
    grade_blocking: bool = False
    judge_explanation: str | None = None
    judge_evidence_lines: list[int] | None = field(default=None)
