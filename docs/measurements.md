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

## M5 — Task 17~21 (2026-08-29, 실행 세션: feat/m5-report-grade)

측정 환경: macOS 호스트 + Docker Compose(이미지 `api/Dockerfile`, gitleaks v8.18.4 동봉,
semgrep·postgres 16 포함). 테스트 136건 전부 green. 실동작 검증은 컨테이너 API(포트 8100)에
zip을 실제로 업로드해 수행했다.

### 게이트 ① 등급 결정론 재현 (P0-3 / B3 DoD)

동일 zip을 **서로 다른 두 스캔**으로 올려 재현성 4축을 비교했다.

| 축 | 스캔 1 | 스캔 2 | 일치 |
| --- | --- | --- | --- |
| `content_fingerprint` | `47877110aeca03aa…` | `47877110aeca03aa…` | ✅ |
| `rule_catalog_version` | `ccbf492fd4e4b464` | `ccbf492fd4e4b464` | ✅ |
| `vuln_db_snapshot_date` | `OSV@2026-08-29; KISA-CSV@2026-08-29` | 동일 | ✅ |
| **`grade`** | **위험** | **위험** | ✅ |

유닛 레벨에서는 `calc_grade`를 50회 반복해 동일 등급을 단언하고(`test_determinism_same_input_same_grade`),
파이프라인 레벨에서는 **LLM 스텁 응답을 실행마다 다르게** 주입한 2회 스캔이 같은 등급을 내는지
단언한다(`test_pipeline_grade_deterministic_across_llm_outputs`). 구조적 보장은 `calc_grade`의
시그니처 자체다 — 인자가 `(status, rule_id, severity, id)`·`(cve_id, cvss_severity)`뿐이라
LLM 산출물이 등급에 닿을 경로가 없다.

### 게이트 ②~⑤ 실동작 결과 (fixture: 시크릿·SQLi·PII·취약 의존성 포함 zip)

| 게이트 | 결과 |
| --- | --- |
| ② 등급 상향 조건 | 위험 스캔 → `{"target":"주의","count":1,"blocking_finding_ids":[10]}`. 주의 스캔 → "이 18건만 해결하면 안심으로 올라갑니다"(발견 12 + CVE 6) |
| ③ 이중 리포트 + 수정 프롬프트 | 발견 14건 전부 `standard_ref` 보유, 전부 `fix_prompt`·`easy_description` 채워짐. easy 응답은 4키(`grade`·`disclaimer`·`easy_descriptions`·`review_needed_count`) |
| ④ 체크리스트 API | 13항목, 전 항목 조항 표기, 200 |
| ⑤ 재진단 diff 3분류 | 시크릿 제거 zip 재업로드 → **위험 → 주의**, `fingerprint_changed=true`, 해결 2·잔여 12·신규 1 |

부수 확인: SEC-04의 `evidence`가 `****`로 마스킹된 채 리포트에 실림(G2), OSV+KISA 교차로
SCA-03 "국내 보안공지 발령" finding 생성, `report_json`이 `parse_markers`·`osv_incomplete`·
`matrix_0322` 스크래치 키를 보존한 채 병합됨(`/sbom` 정상).

### 보류·이월 항목

- **§11 항목 1(LLM 실호출 실측) — 여전히 보류.** `.env`의 `ANTHROPIC_API_KEY`가 플레이스홀더라
  실호출이 401로 떨어진다. Task 18의 변환 결과는 전부 **규칙 기반 폴백 문구**로 채워졌다
  (설계상 의도된 경로 — 리포트가 비지 않는다). 키 준비 후 배치당 토큰·소요·비용 측정 필요.
- **M4 결함 발견(M5 범위 밖, 미수정): gitleaks finding의 `file_path`가 워크스페이스 절대경로.**
  `app/engine/gitleaks_runner.py`가 `-s <절대 임시경로>`로 실행해 gitleaks의 `File` 필드를 그대로
  싣고(`pii.classify_secret`이 `file_path=raw.file`), semgrep 계열(상대경로)과 표기가 갈린다.
  임시 디렉토리명이 스캔마다 무작위라 **diff 키 `(rule_id, file_path, line)`가 스캔 간 절대
  불일치**한다 — 실측: 동일 zip 재진단(지문 무변경)에서 SEC-04가 `해결 1건 + 신규 1건`으로
  잡혔다(코드가 그대로인데 개선으로 보고됨). 리포트에도 `/tmp/ansim-scan-*/src/app/settings.py`가
  노출된다. 수정 지점은 M4 파일이라 이 세션에서 손대지 않았다 — **별도 승인 필요**.
- 참고 특성(스펙대로 동작): diff 키에 `line`이 들어가 있어(TDD §4.7) 같은 결함이라도 줄 번호가
  밀리면 `해결 + 신규`로 계산된다. 실측에서 `DEBUG = True`가 2행→3행으로 이동하자 AUX-02가
  그렇게 잡혔다. 스펙 변경 없이는 불가피하다.
