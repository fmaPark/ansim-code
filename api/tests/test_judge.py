"""Task 16 — LLM judge: 12 병렬·review_needed 고정(G3)·캐시 폴백·모델 ID 기록(G9)·마스킹 2차 패스.

LlmClient는 transport 주입 지점을 갖는다 — 실 API 없이 fake transport로 경계를 검증한다.
실호출 실측(Step 4)은 ANTHROPIC_API_KEY 준비 후 별도 수행(계획 문서에 보류 표기).
"""
import json
from types import SimpleNamespace

import pytest

from app.engine.findings import FindingDraft
from app.engine.masking import MaskRegistry
from app.llm.client import LlmClient, LlmResponse

FAKE_MODEL = "claude-sonnet-5-20260101"   # API 응답이 주는 값 — 설정값과 달라야 G9 검증이 됨
SECRET = "Sup3rSecret99"


def draft(rule_id="P2", status="review_needed", file_path="a.py", line=3):
    return FindingDraft(rule_id, "high", file_path, line, "evidence", status)


class FakeTransport:
    def __init__(self, text=None, fail=False):
        self.calls = []
        self.fail = fail
        self.text = text or json.dumps(
            {"is_likely_issue": False, "explanation": "오탐으로 보입니다.", "evidence_lines": [3]})

    async def __call__(self, model, system, user, max_tokens):
        self.calls.append({"model": model, "system": system, "user": user})
        if self.fail:
            raise RuntimeError("api down")
        return LlmResponse(text=self.text, model_id=FAKE_MODEL, in_tokens=100, out_tokens=30)


@pytest.fixture
def judge_env(tmp_path):
    transport = FakeTransport()
    client = LlmClient(cache_dir=str(tmp_path / "cache"), transport=transport)
    registry = MaskRegistry()
    registry.add(SECRET)
    scan = SimpleNamespace(llm_model_id=None)
    drafts = [draft(rule_id="P2"), draft(rule_id="P10", line=None)]
    snippets = {id(d): f"line1\npw = {SECRET}\nline3" for d in drafts}
    return SimpleNamespace(scan=scan, drafts=drafts, snippets=snippets,
                           client=client, registry=registry, transport=transport,
                           fake_response_model=FAKE_MODEL)


async def _run(env, drafts=None):
    from app.llm.judge import judge_findings

    await judge_findings(env.scan, drafts if drafts is not None else env.drafts,
                         env.snippets, client=env.client, registry=env.registry)


@pytest.mark.asyncio
async def test_judge_never_promotes_status(judge_env):
    # fake 응답이 is_likely_issue=false여도 status는 review_needed 유지 (G3 — 강등도 불가)
    drafts = [draft(rule_id="P2", status="review_needed")]
    judge_env.snippets[id(drafts[0])] = "x = 1"
    await _run(judge_env, drafts)
    assert drafts[0].status == "review_needed"
    assert drafts[0].judge_explanation            # 설명은 채워짐
    assert drafts[0].judge_evidence_lines == [3]


@pytest.mark.asyncio
async def test_sec_rules_skipped(judge_env):
    # G2: SEC-*는 LLM 후보에서 원천 제외 — judge가 받아도 전송하지 않는다
    drafts = [draft(rule_id="SEC-01", status="confirmed")]
    await _run(judge_env, drafts)
    assert judge_env.transport.calls == []
    assert drafts[0].judge_explanation is None


@pytest.mark.asyncio
async def test_payload_masked_before_send(judge_env):
    # P0-2 2차 패스: 전송 직전 registry.mask() 강제 — 페이로드에 시크릿 원문 0건
    await _run(judge_env)
    assert judge_env.transport.calls
    for c in judge_env.transport.calls:
        assert SECRET not in c["user"] and SECRET not in c["system"]


@pytest.mark.asyncio
async def test_model_id_recorded_from_response(judge_env):
    await _run(judge_env)
    assert judge_env.scan.llm_model_id == judge_env.fake_response_model  # 하드코딩 아님 (G9)


@pytest.mark.asyncio
async def test_cache_fallback_on_api_error(tmp_path):
    # 1회차: 정상 응답 → 캐시 기록. 2회차: API 예외 강제 → 캐시로 동일 응답 (TDD §6 폴백)
    cache = str(tmp_path / "cache")
    ok = LlmClient(cache_dir=cache, transport=FakeTransport())
    r1 = await ok.complete("m", "sys", "user payload", 256)
    down = LlmClient(cache_dir=cache, transport=FakeTransport(fail=True))
    r2 = await down.complete("m", "sys", "user payload", 256)
    assert r2.text == r1.text and r2.model_id == r1.model_id

    with pytest.raises(RuntimeError):             # 캐시도 없으면 예외 전파
        await down.complete("m", "sys", "다른 payload", 256)


@pytest.mark.asyncio
async def test_cost_counters(judge_env):
    await _run(judge_env)
    stats = judge_env.client.stats()
    assert stats["calls"] == len(judge_env.transport.calls) > 0
    assert stats["in_tokens"] == 100 * stats["calls"]


@pytest.mark.asyncio
async def test_bad_json_retried_once_then_given_up(tmp_path):
    transport = FakeTransport(text="이건 JSON이 아님")
    client = LlmClient(cache_dir=str(tmp_path / "c"), transport=transport)
    env = SimpleNamespace(scan=SimpleNamespace(llm_model_id=None), client=client,
                          registry=MaskRegistry(), transport=transport)
    d = draft(rule_id="P2")
    env.snippets = {id(d): "x = 1"}
    from app.llm.judge import judge_findings

    await judge_findings(env.scan, [d], env.snippets, client=client, registry=env.registry)
    assert len(transport.calls) == 2              # 1회 재요청 후 포기
    assert d.judge_explanation is None            # 설명 없이 유지 — 파이프라인은 계속
    assert d.status == "review_needed"


# ── run_llm_stage 통합 (P1·P4 합성 + 스니펫 + judge) ─────────────────────────

@pytest.mark.asyncio
async def test_llm_stage_synthesizes_p1_p4_and_masks(tmp_path):
    from app.engine.analysis import run_llm_stage

    (tmp_path / "collect.py").write_text(
        'import requests\n\ndef send(request):\n'
        f'    phone = request.form["phone"]  # {SECRET}\n'
        '    requests.post("https://x.example", data={"phone": phone})\n')
    transport = FakeTransport()
    client = LlmClient(cache_dir=str(tmp_path / "c"), transport=transport)
    registry = MaskRegistry()
    registry.add(SECRET)
    scan = SimpleNamespace(llm_model_id=None)
    drafts = [FindingDraft("P2", "high", "collect.py", 4, 'request.form["phone"]', "review_needed"),
              FindingDraft("SEC-01", "critical", "collect.py", 4, "KEY = ****", "confirmed")]
    await run_llm_stage(scan, drafts, tmp_path, registry, client=client)

    by_rule = {d.rule_id for d in drafts}
    assert {"P1", "P4"} <= by_rule                       # 합성 발견 생성
    assert all(d.status == "review_needed" for d in drafts if d.rule_id in {"P1", "P2", "P4"})
    sent = "\n".join(c["user"] for c in transport.calls)
    assert SECRET not in sent                            # 스니펫 마스킹 (P0-2 2차)
    assert "SEC-01" not in sent                          # G2: SEC-* 미전송
    assert scan.llm_model_id == FAKE_MODEL
