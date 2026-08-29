"""Task 18 — 쉬운 한국어 + 수정 프롬프트 배치 생성(haiku·30항목).

배치 분할·id 매핑·불일치 폴백·마스킹(P0-2 재확인)을 fake transport로 검증한다.
실호출 실측은 ANTHROPIC_API_KEY 준비 후 별도 수행(계획 문서 실측 기록에 보류 표기).
"""
import json
from types import SimpleNamespace

import pytest

from app.config import settings
from app.engine.masking import MaskRegistry
from app.llm.client import LlmClient, LlmResponse
from app.llm.convert import generate_texts

FAKE_MODEL = "claude-haiku-4-5-20260101"   # 설정값과 달라야 G9 검증이 된다
SECRET = "Sup3rSecret99"


def finding(i, rule_id="AUX-02", file_path="a.py", line=3, evidence="evidence"):
    """Finding ORM 행을 대신하는 최소 객체 — generate_texts는 속성만 읽고 쓴다."""
    return SimpleNamespace(id=i, rule_id=rule_id, severity="medium", file_path=file_path,
                           line=line, evidence=evidence, status="confirmed",
                           easy_description=None, fix_prompt=None)


class FakeTransport:
    """요청받은 id를 그대로 되돌려주는 transport. respond로 응답 전략을 바꾼다."""

    def __init__(self, respond=None):
        self.calls = []
        self._respond = respond or self._echo

    @staticmethod
    def _echo(ids):
        return json.dumps([{"id": i, "easy": f"쉬운 설명 {i}", "fix_prompt": f"수정 지시 {i}"}
                           for i in ids])

    async def __call__(self, model, system, user, max_tokens):
        self.calls.append({"model": model, "system": system, "user": user})
        ids = [item["id"] for item in json.loads(user[user.index("["):user.rindex("]") + 1])]
        return LlmResponse(text=self._respond(ids), model_id=FAKE_MODEL,
                           in_tokens=200, out_tokens=400)


def _env(tmp_path, respond=None):
    transport = FakeTransport(respond)
    client = LlmClient(cache_dir=str(tmp_path / "cache"), transport=transport)
    registry = MaskRegistry()
    registry.add(SECRET)
    scan = SimpleNamespace(llm_model_id=None)
    return SimpleNamespace(scan=scan, client=client, registry=registry, transport=transport)


@pytest.mark.asyncio
async def test_batches_31_findings_into_two_calls(tmp_path):
    env = _env(tmp_path)
    findings = [finding(i) for i in range(1, 32)]

    await generate_texts(env.scan, findings, client=env.client, registry=env.registry)

    assert settings.convert_batch_size == 30
    assert len(env.transport.calls) == 2                 # 30 + 1
    assert all(c["model"] == settings.convert_model for c in env.transport.calls)


@pytest.mark.asyncio
async def test_maps_response_to_matching_finding(tmp_path):
    env = _env(tmp_path)
    findings = [finding(7), finding(9)]

    await generate_texts(env.scan, findings, client=env.client, registry=env.registry)

    assert findings[0].easy_description == "쉬운 설명 7"
    assert findings[0].fix_prompt == "수정 지시 7"
    assert findings[1].easy_description == "쉬운 설명 9"
    assert env.scan.llm_model_id == FAKE_MODEL           # G9: 응답의 model 필드 기록


@pytest.mark.asyncio
async def test_mismatched_response_retries_once_then_falls_back(tmp_path):
    env = _env(tmp_path, respond=lambda ids: json.dumps([{"id": 999, "easy": "x",
                                                          "fix_prompt": "y"}]))
    f = finding(1, rule_id="AUX-02", file_path="settings.py", line=12)

    await generate_texts(env.scan, [f], client=env.client, registry=env.registry)

    assert len(env.transport.calls) == 2                 # 불일치 → 배치 1회 재시도
    assert "디버그 모드 활성" in f.easy_description        # 카탈로그 title 기반 폴백
    assert "settings.py:12" in f.easy_description
    assert "TTAK.KO-11.0259" in f.fix_prompt              # 근거 조항 포함
    assert f.easy_description and f.fix_prompt            # 리포트가 비지 않는다(DoD)


@pytest.mark.asyncio
async def test_payload_is_masked_before_send(tmp_path):
    env = _env(tmp_path)
    f = finding(1, evidence=f'API_KEY = "{SECRET}"')

    await generate_texts(env.scan, [f], client=env.client, registry=env.registry)

    assert SECRET not in env.transport.calls[0]["user"]   # P0-2 2차 패스
    assert SECRET not in env.transport.calls[0]["system"]


@pytest.mark.asyncio
async def test_no_client_falls_back_for_every_finding(tmp_path, monkeypatch):
    """키가 없어도 모든 finding에 두 텍스트가 존재해야 한다(DoD — judge와 다른 정책)."""
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    scan = SimpleNamespace(llm_model_id=None)
    findings = [finding(1), finding(2, rule_id="P9", file_path=None, line=None)]

    await generate_texts(scan, findings)

    assert all(f.easy_description and f.fix_prompt for f in findings)
    assert "(저장소 전체)" in findings[1].easy_description
