---
type: Note
title: 실측 기록 (measurements)
description: 계획 §11 항목 1·3·5 및 M7 검증의 실측치를 태스크 완료 시점마다 append하는 기록부.
status: living
tags: [ansimcode, measurements]
---

# 실측 기록

> 계획(docs/plans/mvp-implementation.md) '실측 기록' 섹션의 상세본. 실행 세션이 append한다.

## M4 — Task 16 (2026-08-29, 실행 세션: feat/m4-rules-llm)

측정 환경: 리눅스 샌드박스(Python 3.10, semgrep 1.175.0 pip 설치). gitleaks 바이너리는
샌드박스 반입 불가(프록시가 릴리스 바이너리 차단) — Docker 이미지(v8.18.4 동봉) 안 재측정 필요.

### §11 항목 1 — LLM 호출 상한 (fake transport 기준, **실호출 실측은 보류**)

| 항목 | 값 | 비고 |
| --- | --- | --- |
| judge 동시성 | 12 (`settings.judge_concurrency`) | Semaphore 동작 검증: 24건 × 호출당 1.0s 모사 지연 → wall 2.02s (이론치 2.0s와 일치 — 병렬화 오버헤드 무시 가능) |
| judge 호출당 토큰 (fake) | in 800 / out 120 (모사값) | 실호출 시 실제 스니펫(±10줄) 기준 재측정 필요 |
| **실호출 소요·비용** | **보류** | ANTHROPIC_API_KEY 미준비(.env 없음 — .env.example만 존재). 키 준비 후 fixture 스캔 1회로 judge 12 병렬 소요·토큰·비용 기록 예정 |

### §11 항목 3 — gitleaks 오탐(allowlist) 실측

**보류** — gitleaks 바이너리가 샌드박스에 없어 allowlist 통과 플레이스홀더 목록 실측 불가.
Docker 이미지 안에서 `pytest tests/test_gitleaks.py`(skipif 해제분 2케이스) + fixture 스캔으로 측정 예정.
초기 allowlist(G13): `your-api-key`·`changeme`·`sk-test-`·`example`(소문자 한정)·`dummy`·`<...>` + docs/README/fixtures 경로.

### 정적 스테이지 소요 (참고 — G14 예산 배분용)

| 단계 | 소요 | 조건 |
| --- | --- | --- |
| semgrep (privacy+aux 자체 룰 9종) | 1.24s | fixture 10파일, 7 hits |
| repo_checks (P5·P7~P10) | 1ms | fixture 10파일, 5 drafts |

### §11 항목 2 — 벤치마크 취약점 목록

**기획 확정 재요청 (M4 완료 시점 — M7 착수 전 마감 게이트).** 미수신 시 폴백:
개발이 룰 커버리지 기준 초안(`expected_findings.yaml`) 작성 → 기획 승인만 받는다.
