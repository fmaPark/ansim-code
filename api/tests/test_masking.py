"""Task 14 — 시크릿 마스킹(P0-2): 저장 마스킹 + LLM 직전 2차 패스 (TDD §8·§9 B2).

계획의 pipeline_result / pipeline_with_llm_stub 픽스처는 DB 없이 돌 수 있게
정적 분석 스테이지 함수(run_static_stage)와 LLM 후보 필터(llm_candidates)를
직접 구동하는 형태로 구현했다(gitleaks subprocess는 스텁 — 샌드박스에 바이너리 없음).
"""
import json
import subprocess

import pytest

from app.engine.masking import MaskRegistry, mask_value

SECRET = "Sup3rSecret99"
AKIA = "AKIAIOSFODNN7EXAMPLE"


def test_masking_removes_all_occurrences():
    reg = MaskRegistry()
    reg.add(SECRET)
    reg.add(AKIA)
    out = reg.mask(f"pw={SECRET} # key {AKIA} and again {SECRET}")
    assert SECRET not in out and "AKIA" not in out
    assert out.count("****") == 3


def test_mask_value_longest_first():      # 부분 겹침: 긴 시크릿부터 치환
    out = mask_value("token=abcdef1234 abcdef", ["abcdef", "abcdef1234"])
    assert "abcdef" not in out and out.count("****") == 2


@pytest.fixture
def pipeline_result(tmp_path, monkeypatch):
    """fixture에 시크릿을 심고 정적 스테이지 실행 (gitleaks 경계는 스텁)."""
    (tmp_path / "db.py").write_text(f"# prod db password = {SECRET}\nx=1\n")
    findings_json = [
        {"RuleID": "ansim-comment-secret", "File": "db.py", "StartLine": 1,
         "Secret": SECRET, "Match": f"# prod db password = {SECRET}"},
        {"RuleID": "aws-access-token", "File": "db.py", "StartLine": 1,
         "Secret": AKIA, "Match": f'KEY = "{AKIA}"'},
    ]

    def fake_run(cmd, **kw):
        if cmd[0] == "semgrep":   # Task 15 이후 static stage가 semgrep도 부른다 — 빈 결과 스텁
            return subprocess.CompletedProcess(cmd, 0, stdout=b'{"results": []}', stderr=b"")
        with open(cmd[cmd.index("-r") + 1], "w") as f:
            json.dump(findings_json, f)
        return subprocess.CompletedProcess(cmd, 1, stdout=b"", stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    from app.engine.analysis import run_static_stage

    return run_static_stage(tmp_path)


def test_evidence_stored_masked(pipeline_result):   # 통합: fixture에 시크릿 심고 스캔
    drafts, registry = pipeline_result
    assert drafts                                    # 시크릿 finding이 실제로 생겼고
    for f in drafts:
        assert SECRET not in (f.evidence or "")      # ① 저장 마스킹 (G2)
        assert AKIA not in (f.evidence or "")


def test_llm_payload_has_no_secret(pipeline_result):
    # LLM 전송 직전 2차 패스(TDD §9 B2 DoD) — client(Task 16)가 강제 호출하는 경계 함수
    _, registry = pipeline_result
    payload = f"진단 스니펫:\n# prod db password = {SECRET}\nKEY={AKIA}"
    out = registry.mask(payload)
    assert SECRET not in out and AKIA not in out


def test_secret_rules_never_reach_llm(pipeline_result):
    from app.engine.analysis import llm_candidates

    drafts, _ = pipeline_result
    sent_rule_ids = [d.rule_id for d in llm_candidates(drafts)]
    assert not any(r.startswith("SEC-") for r in sent_rule_ids)   # G2 미경유
