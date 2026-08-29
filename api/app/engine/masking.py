"""시크릿 마스킹 (P0-2, Task 14) — TDD §8.

적용 지점 2곳:
  ① Finding.evidence 저장 직전(모든 룰) — analysis.run_static_stage
  ② LLM 페이로드 조립 직후·전송 직전 — llm.client가 registry.mask()를 강제 호출(2차 패스)
검출 시크릿 원문은 MaskRegistry 인메모리에만 존재하고 스캔 종료와 함께 사라진다.
"""
MASK = "****"


def mask_value(text: str, secrets: list[str]) -> str:
    """등장 시크릿을 ****로 치환. 긴 것부터 치환해 부분 겹침을 방지한다."""
    for s in sorted({s for s in secrets if s}, key=len, reverse=True):
        text = text.replace(s, MASK)
    return text


class MaskRegistry:
    """스캔 단위 시크릿 원문 수집처(메모리 전용 — G2: DB·로그·리포트 기록 금지)."""

    def __init__(self) -> None:
        self._secrets: set[str] = set()

    def add(self, secret: str) -> None:
        if secret:
            self._secrets.add(secret)

    def mask(self, text: str) -> str:
        return mask_value(text, list(self._secrets))

    def __len__(self) -> int:
        return len(self._secrets)
