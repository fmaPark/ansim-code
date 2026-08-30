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

~~**보류**~~ → **해소(이슈 #15)** — 아래 "이슈 #13·#15" 섹션에 확정치 기록 (2026-08-29).
당시 상황: gitleaks 바이너리가 샌드박스에 없어 allowlist 통과 플레이스홀더 목록 실측 불가.
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
- **M4 결함 발견(M5 범위 밖, 미수정 → 이슈 #13으로 이관, 2026-08-29 수정 완료 — 아래 섹션):
  gitleaks finding의 `file_path`가 워크스페이스 절대경로.**
  `app/engine/gitleaks_runner.py`가 `-s <절대 임시경로>`로 실행해 gitleaks의 `File` 필드를 그대로
  싣고(`pii.classify_secret`이 `file_path=raw.file`), semgrep 계열(상대경로)과 표기가 갈린다.
  임시 디렉토리명이 스캔마다 무작위라 **diff 키 `(rule_id, file_path, line)`가 스캔 간 절대
  불일치**한다 — 실측: 동일 zip 재진단(지문 무변경)에서 SEC-04가 `해결 1건 + 신규 1건`으로
  잡혔다(코드가 그대로인데 개선으로 보고됨). 리포트에도 `/tmp/ansim-scan-*/src/app/settings.py`가
  노출된다. 수정 지점은 M4 파일이라 이 세션에서 손대지 않았다 — **별도 승인 필요**.
- 참고 특성(스펙대로 동작): diff 키에 `line`이 들어가 있어(TDD §4.7) 같은 결함이라도 줄 번호가
  밀리면 `해결 + 신규`로 계산된다. 실측에서 `DEBUG = True`가 2행→3행으로 이동하자 AUX-02가
  그렇게 잡혔다. 스펙 변경 없이는 불가피하다.

## 이슈 #13·#15 (2026-08-29, 실행 세션: claude/fix-issues-13-15-3cbb4c)

측정 환경: macOS 호스트 + Docker Compose(gitleaks v8.18.4 동봉 이미지). 실행 커맨드:

```
docker compose run --rm -v "$PWD:/work" -w /work/api -e RULES_DIR=/work/rules api pytest tests/test_gitleaks.py -v -s
```

### 이슈 #13 — gitleaks `file_path` 상대경로 정규화 (수정 완료)

`run_gitleaks`가 gitleaks `File`(절대경로)을 `root` 기준 상대경로로 정규화하도록 수정
(semgrep 러너와 동일 이디엄: `relative_to(root).as_posix()`, root 밖 경로는 그대로 폴백).
실바이너리 회귀 검증: 동일 콘텐츠를 서로 다른 두 워크스페이스에서 스캔 →
`(rule_id, file, line)` 키 집합 일치 + `diff_findings` 전량 `remaining`
(`test_rescan_workspaces_yield_identical_keys`). 재진단 통합 테스트에도
지문 무변경 시 `resolved_count == 0`·`new_count == 0` 단언 추가(`test_rescan.py`).

### 이슈 #15 — §11 항목 3 allowlist 오탐률 확정치

플레이스홀더 코퍼스 15종(주석 시크릿형 9 + `.env` 2 + docs/README 경로 2 + 더미 전화·주민번호 2)
+ 대조군 4종(형식-유효 AKIA 키·주석 실비밀번호·실`.env`·유효 체크섬 주민번호)으로
`test_allowlist_placeholder_pass_rate`가 측정·회귀 고정한다. baseline(allowlist 제거 설정)
스캔으로 코퍼스 전원이 hit 후보임을 자체 검증한 뒤 통과율을 계산한다.

| 시점 | allowlist 적중률 | 잔여 오탐 |
| --- | --- | --- |
| 보강 전 (G13 초기 목록) | **8/15 (53%)** | `.env.example` 커밋, `REPLACE_ME`, `your-secret-*`, `sample`, `placeholder`, `010-1234-5678`, `123456-1234567` |
| 보강 후 | **15/15 (100%)** | 없음 — 대조군 4종 전부 계속 탐지(과확장 없음) |

보강 내역(`rules/gitleaks/ansim.toml` `[allowlist]`):
`your[-_]?api[-_]?key` → `your[-_]?(api[-_]?key|key|secret|token|password)` 확장,
`(?i)replace[-_]me`(구분자 필수로 형식-유효 키 충돌 차단)·`sample`·`placeholder`(소문자 한정
원칙 유지)·관습적 더미 전화번호(`010-1234-5678`)·더미 주민번호(`123456-1234567`) regex 추가,
paths에 `\.env\.example$` 추가. 형식-유효 `AKIA…EXAMPLE` 탐지 유지는
`test_hardcoded_key_detected_placeholder_ignored`가 계속 고정한다.

skipif 2케이스(주석 시크릿·플레이스홀더 무시)도 컨테이너 안에서 해제 실행 — green.

## M6 — Task 22~25 (2026-08-29, 실행 세션: feat/m6-frontend)

측정 환경: 로컬 Docker Compose(맥 호스트). 다른 워크트리 스택이 8000·8080을 점유해
로컬 오버라이드로 api 8001·web 8085 사용(커밋 안 함 — 기본 포트 매핑은 불변).
브라우저 검증은 Claude 브라우저 자동화(실 Chromium)로 수행.

### M6 게이트 — 전 흐름 연속 완주: **통과**

`https://github.com/fmaPark/ansim-publish-test`(검증용 공개 repo, 사용자 승인 후 생성)로
업로드 → 진행 단계 → 리포트 → 복사 → 공개(.ansimcode) → 배지 → 재진단 diff를 한 번에 완주.
공개 2단계는 모킹 없이 **실제 shallow clone으로 `.ansimcode` 토큰 대조**에 성공했다.

### Task 23 수동 체크리스트 (5/5 통과)

| # | 항목 | 결과 |
| --- | --- | --- |
| ① | git URL 제출 → 진행 화면 전환 | ✅ `/scan/{id}` 전환, 완료 시 `/report/{id}` 자동 이동 |
| ② | zip 드래그 앤 드롭 | ✅ DataTransfer drop 이벤트로 검증(자동화 제약상 합성 이벤트 — 동일 핸들러 경유) |
| ③ | 60MB 더미 zip 거부 | ✅ "zip은 50MB 이하만 지원합니다 (업로드 파일: 60.0MB)" 즉시 표시(서버 미호출) |
| ④ | 잘못된 URL 배너 | ✅ http:// URL → "공개 https git URL만 지원합니다" 배너 |
| ⑤ | 스텝퍼 단계 반영 | ✅ pallets/click 스캔 중 환경분석·현황진단 done → 위험분석 active 관찰 |

### Task 24 수동 체크리스트 (7/7 통과)

| # | 항목 | 결과 |
| --- | --- | --- |
| ① | 등급·상향 블록 | ✅ 위험 GradePill + "이 1건만 해결하면 주의로 올라갑니다" + 발견/CVE 앵커 |
| ② | 항목별/전체 복사 | ✅ 복사 텍스트 내용 검증(전체 10줄·항목별). 자동화 샌드박스가 클립보드 권한을 차단해 실제 클립보드 기록은 확인 불가 — clipboard→execCommand→prompt 3단 폴백 구현 |
| ③ | easy 토글 | ✅ 쉬운 설명 요약 카드 + 카드별 evidence 숨김·easy_description만 표시 |
| ④ | SBOM JSON 다운로드 | ✅ Blob 내용 검증(파일명·application/json·4키·컴포넌트 목록) — 샌드박스가 실제 저장은 차단 |
| ⑤ | review_needed 뱃지·병기 | ✅ SEC-05 휴대전화 → "검토 필요" 뱃지 + 상단 "AI 검토가 필요한 항목 1건" 스트립 |
| ⑥ | 재진단 diff | ✅ 시크릿+PII 제거 zip 재업로드 → 위험→주의, 해결 4·잔여 6·신규 2. 같은 zip 재업로드 → "코드 변경 없음" + 해결 0·잔여 8·신규 0 |
| ⑦ | disclaimer 상시 | ✅ 상단 스트립 + 하단, easy 토글·전 탭에서 유지 |

### Task 25 수동 체크리스트 (5/5 통과)

| # | 항목 | 결과 |
| --- | --- | --- |
| ① | 실공개 2단계 성공 | ✅ 토큰 발급 → `.ansimcode` 커밋·푸시 → 확인 → 공개 URL·배지 마크다운 표시 |
| ② | 배지 렌더 | ✅ SVG가 브라우저에서 "안심코드 \| 주의 2026-08-29"로 렌더(폭 140→170 보정 후). GitHub 원격 README 미리보기는 URL이 localhost라 불가(ADR §5 로컬 데모 한계 — 마크다운 문법·이미지 렌더는 로컬 확인) |
| ③ | 잘못된 토큰 409 | ✅ 커밋 전 확인 → ".ansimcode 토큰이 일치하지 않습니다..." + 같은 토큰으로 재시도 가능 |
| ④ | zip 비활성+안내 | ✅ 버튼 비활성 + ZIP_PUBLISH_NOTICE 툴팁, 직접 API 호출 시 403 + 동일 detail |
| ⑤ | `/g/{slug}` 시민 화면 | ✅ 큰 GradePill·쉬운 설명 목록·재현성 4종 접기·법적 고지 상시·"소유자가 직접 공개" 표기 |

### 보류·이월 항목

- **§11 항목 7·8 카피 미수신(게이트 확인 완료)** — placeholder 유지. 교체 지점:
  `api/app/routes/public.py`의 `LEGAL_NOTICE`·`ZIP_PUBLISH_NOTICE` + `web/src/components/PublishFlow.tsx` 미러 1곳. 항목 4(주민번호 무효)도 미수신 — review_needed 기본값 유지.
- **gitleaks·PII 절대경로 file_path(M5 이월) — #18 머지 반영으로 해소 확인(2026-08-30).**
  이 세션은 미수정 방침이었고(다른 워크트리 픽스 선머지), main(#18) 머지 후 재검증:
  시크릿+PII zip 스캔에서 SEC-04·05 `file_path=app/settings.py`(상대경로) 기록,
  **같은 zip 재진단이 해결 0·잔여 10·신규 0**(이전 오보: SEC 해결+신규 쌍) — 이슈 #13 해소.
  `pii.py`는 gitleaks 러너의 `RawSecret.file`을 그대로 소비하므로 러너 1곳 수정으로 SEC-05까지 커버됨을 코드로 확인.
  머지 후 전체 테스트 146건 green(`RULES_DIR`를 머지된 rules로 지정해 컨테이너 실행).
- **diff 키(rule_id, file_path, line)의 라인 이동 민감성(신규 관찰)** — v3→v4 재진단에서 코드 수정으로
  라인이 2줄 밀리자 AUX-01·02가 '해결+신규' 쌍으로 잡혔다. 카운트는 정직하나 데모 내레이션 시
  "동일 룰 해결+신규 쌍 = 위치 이동"임을 언급할 것. 개선은 M6 범위 밖(백엔드 diff.py).
- **LLM 실호출(§11 항목 1)** — `.env` 키 placeholder(401) → 전 스캔이 폴백 경로. M7 데모 전 실키 필수.
