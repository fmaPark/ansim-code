"""Anthropic 클라이언트 래퍼 (Task 16) — TDD §4.2·§6·§8·§10.

- temperature=0, 타임아웃 60s (G9)
- 전송 직전 registry.mask() 강제 적용 — P0-2 2차 패스 (Task 14)
- 성공 응답은 sha256(model+system+user) 키로 캐시(record), API 예외 시 캐시 폴백(TDD §6
  — 실호출 우선·장애 시에만), 캐시도 없으면 예외 전파
- 호출 수·토큰 누계 인메모리 카운터 + 구조화 로그 (§10)
- transport 주입 지점: 테스트는 fake transport로 API 경계를 대체한다
"""
import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from app.config import settings

log = logging.getLogger(__name__)

LLM_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class LlmResponse:
    text: str
    model_id: str        # API 응답의 model 필드 그대로 (G9 — 하드코딩 금지)
    in_tokens: int
    out_tokens: int


class LlmClient:
    def __init__(self, api_key: str | None = None, cache_dir: str | None = None,
                 transport=None):
        self._api_key = api_key if api_key is not None else settings.anthropic_api_key
        self._cache_dir = Path(cache_dir or settings.llm_cache_dir)
        self._transport = transport or self._anthropic_transport
        self._calls = 0
        self._in_tokens = 0
        self._out_tokens = 0

    # ── 실제 API 경계 (테스트에서는 transport 주입으로 대체) ──
    async def _anthropic_transport(self, model, system, user, max_tokens) -> LlmResponse:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self._api_key, timeout=LLM_TIMEOUT_SECONDS)
        resp = await client.messages.create(
            model=model, system=system, max_tokens=max_tokens,
            temperature=0,                                   # G9
            messages=[{"role": "user", "content": user}])
        return LlmResponse(
            text="".join(b.text for b in resp.content if getattr(b, "type", "") == "text"),
            model_id=resp.model,                             # G9: 응답의 model 필드 기록
            in_tokens=resp.usage.input_tokens,
            out_tokens=resp.usage.output_tokens)

    def _cache_path(self, model, system, user) -> Path:
        key = hashlib.sha256(f"{model}\x00{system}\x00{user}".encode()).hexdigest()
        return self._cache_dir / f"{key}.json"

    async def complete(self, model: str, system: str, user: str, max_tokens: int = 1024,
                       registry=None) -> LlmResponse:
        if registry is not None:                             # P0-2 ② 전송 직전 2차 마스킹 패스
            system = registry.mask(system)
            user = registry.mask(user)
        cache = self._cache_path(model, system, user)
        try:
            resp = await self._transport(model, system, user, max_tokens)
        except Exception as e:
            if cache.is_file():                              # TDD §6: 장애 시에만 캐시 폴백
                log.warning("LLM 장애 — 캐시 폴백", extra={"error": type(e).__name__})
                return LlmResponse(**json.loads(cache.read_text()))
            raise
        self._calls += 1
        self._in_tokens += resp.in_tokens
        self._out_tokens += resp.out_tokens
        log.info("llm call", extra={"model_id": resp.model_id, "in_tokens": resp.in_tokens,
                                    "out_tokens": resp.out_tokens, "calls_total": self._calls})
        try:                                                 # 성공 응답 record (리허설 폴백 대비)
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(resp.__dict__, ensure_ascii=False))
        except OSError:
            log.warning("llm cache write failed")
        return resp

    def stats(self) -> dict:
        return {"calls": self._calls, "in_tokens": self._in_tokens,
                "out_tokens": self._out_tokens}
