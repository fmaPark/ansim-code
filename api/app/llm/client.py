"""Google Gemini 클라이언트 래퍼 (Task 16 → Task 30 전환) — TDD §4.2·§6·§8·§10.

- temperature=0, 타임아웃 60s (G9). thinking 비활성(thinking_budget=0 — 지연·비용 통제)
- 안전 필터는 전 카테고리 최소 차단 — 시크릿·PII·인젝션 스니펫이 이 제품의 정상 입력이다(§6)
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

# 안전 필터 최소 차단 (TDD §6) — 진단 대상 스니펫은 시크릿·주민번호·인젝션 페이로드다.
# 차단되면 judge 설명이 통째로 누락되므로 전 카테고리를 BLOCK_NONE으로 연다.
# 등급에는 영향이 없다 — LLM 경유 발견은 항상 review_needed(G3 §4.5).
SAFETY_OFF_CATEGORIES = (
    "HARM_CATEGORY_HARASSMENT",
    "HARM_CATEGORY_HATE_SPEECH",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "HARM_CATEGORY_DANGEROUS_CONTENT",
    "HARM_CATEGORY_CIVIC_INTEGRITY",
)


class LlmBlockedError(RuntimeError):
    """안전 필터 등으로 본문이 비어 돌아온 응답 — 캐시 폴백 경로를 타게 예외로 올린다."""


@dataclass(frozen=True)
class LlmResponse:
    text: str
    model_id: str        # API 응답의 model_version 필드 그대로 (G9 — 하드코딩 금지)
    in_tokens: int
    out_tokens: int


class LlmClient:
    def __init__(self, api_key: str | None = None, cache_dir: str | None = None,
                 transport=None):
        self._api_key = api_key if api_key is not None else settings.gemini_api_key
        self._cache_dir = Path(cache_dir or settings.llm_cache_dir)
        self._transport = transport or self._gemini_transport
        self._calls = 0
        self._in_tokens = 0
        self._out_tokens = 0

    # ── 실제 API 경계 (테스트에서는 transport 주입으로 대체) ──
    async def _gemini_transport(self, model, system, user, max_tokens) -> LlmResponse:
        # SDK import는 함수 안에서 — 키·SDK 없이도 fake transport 테스트가 돈다
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=self._api_key,
            # SDK의 timeout 단위는 밀리초다 (초를 그대로 넘기면 60ms 타임아웃이 된다)
            http_options=types.HttpOptions(timeout=LLM_TIMEOUT_SECONDS * 1000))
        resp = await client.aio.models.generate_content(
            model=model, contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,                   # 최상위 인자가 아니라 config 안
                max_output_tokens=max_tokens,
                temperature=0,                               # G9
                thinking_config=types.ThinkingConfig(thinking_budget=0),   # 지연·비용 통제
                safety_settings=[types.SafetySetting(category=c, threshold="BLOCK_NONE")
                                 for c in SAFETY_OFF_CATEGORIES]))

        text = resp.text
        if not text:                                         # 안전 필터 차단·빈 후보 (§6)
            cand = (resp.candidates or [None])[0]
            log.warning("LLM 응답 본문 없음 — 차단 가능성", extra={
                "finish_reason": str(getattr(cand, "finish_reason", None)),
                "block_reason": str(getattr(resp.prompt_feedback, "block_reason", None)
                                    if resp.prompt_feedback else None)})
            raise LlmBlockedError("empty response body")

        model_id = resp.model_version
        if not model_id:                    # G9 폴백: 응답에 필드가 없으면 요청 모델 ID + 로그
            log.warning("응답에 model_version 없음 — 요청 모델 ID로 대체", extra={"model": model})
            model_id = model
        usage = resp.usage_metadata
        return LlmResponse(
            text=text,
            model_id=model_id,                               # G9: 응답의 model_version 기록
            in_tokens=getattr(usage, "prompt_token_count", 0) or 0,
            out_tokens=getattr(usage, "candidates_token_count", 0) or 0)

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
