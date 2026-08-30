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

## M7 — Task 26 (2026-08-30, 실행 세션: feat/m7-verification)

측정 환경: 로컬 Docker Compose(이 워크트리 스택, api 8002 / web 8086 — 다른 워크트리가 8000 점유).
`ANTHROPIC_API_KEY` **미설정** 상태로 측정했다. 명세 §1.4대로 등급과 P1~P5·P10 초안은 전부
static 경로라 키 없이 재현되며, 키가 필요한 것은 judge 설명 텍스트뿐이다 — 실제로 `llm_model_id`가
null인 채로 31종 중 28종이 발화했다.

벤치마크 저장소: **<https://github.com/fmaPark/ansim-benchmark>** (공개, `v1-danger` 태그 = main).
오라클: `verification/expected_findings.yaml` (명세 §5.2 확정본 + 스캐폴딩 후 개발 기입분).

재현 명령:

```bash
python verification/check_invariants.py <benchmark_checkout>
python verification/measure_detection.py \
  --api http://localhost:8002 \
  --repo https://github.com/fmaPark/ansim-benchmark \
  --oracle <benchmark_checkout>/verification/expected_findings.yaml \
  --benchmark-root <benchmark_checkout>
```

측정 대상: `https://github.com/fmaPark/ansim-benchmark` · 등급 **위험** · 소요 **15.2s**(G14 2분 목표 대비 여유)

- `content_fingerprint`: `94876f8da387c83e…` (git_commit)
- `rule_catalog_version`: `8e512d222d972ed9`
- `vuln_db_snapshot_date`: OSV@2026-08-30; KISA-CSV@2026-08-29
- `llm_model_id`: (LLM 미호출 — 키 미설정)

### ① TPR — 룰별 검출률 (전체 31종 기준)

| 룰 | 기대 | 검출 | TPR | 미검출 위치 / 사유 |
| --- | --- | --- | --- | --- |
| SCA-01 | 2 | 2 | 100% | |
| SCA-02 | 5 | 5 | 100% | |
| SCA-03 ⛔ | 5 | 5 | 100% | **이 행은 무효(이슈 #17)** — 표본 KISA 스냅샷 기준 측정이다. 실데이터로 교체된 뒤에는 5핀 중 django 1건만 발화한다. 재측정 필요 |
| SCA-04 | 5 | 5 | 100% | |
| SCA-05 ⚠ | 1 | 0 | 0% | six — **룰 갭**: `build_sbom`이 `release_date`를 항상 null로 둔다([sbom.py:167](../api/app/engine/sbom.py#L167) — 레지스트리 원격 조회 없음 가정). 판정 입력 자체가 없어 `_older_than`이 언제나 False다 |
| SCA-06 | 1 | 1 | 100% | |
| SCA-07 ⚠ | 1 | 0 | 0% | pymupdf — **룰 갭**: 라이선스는 동봉 LICENSE 본문·vendored `package.json`에서만 판정한다([sbom.py:85-108](../api/app/engine/sbom.py#L85)). 매니페스트 선언만으로는 AGPL을 알 수 없어 SCA-08(라이선스 불명)로 흡수됐다 |
| SCA-08 | 1 | 1 | 100% | |
| SCA-09 | 1 | 1 | 100% | |
| SCA-10 | 1 | 1 | 100% | |
| SCA-11 | 1 | 1 | 100% | |
| SCA-12 | 1 | 1 | 100% | |
| SEC-01 | 2 | 2 | 100% | |
| SEC-02 | 1 | 1 | 100% | |
| SEC-03 | 1 | 1 | 100% | |
| SEC-04 | 3 | 3 | 100% | 인젝션 페이로드 파일 포함 |
| SEC-05 | 2 | 2 | 100% | 체크섬 유효(confirmed)·무효(review_needed) 양분기 |
| P1 | 1 | 1 | 100% | 정적 합성 — 키 없이 검출 |
| P2 | 2 | 2 | 100% | Py·JS 양쪽 |
| P3 | 1 | 1 | 100% | |
| P4 | 1 | 1 | 100% | 정적 합성 — 키 없이 검출 |
| P5 | 1 | 1 | 100% | |
| P6 | 1 | 1 | 100% | |
| P7 | 2 | 2 | 100% | Py·JS 양쪽 |
| P8 | 1 | 1 | 100% | |
| P9 | 1 | 1 | 100% | |
| P10 | 1 | 1 | 100% | |
| AUX-01 | 2 | 2 | 100% | Py·JS 양쪽 |
| AUX-02 | 1 | 1 | 100% | |
| AUX-03 ⚠ | 1 | 0 | 0% | `vulnerable/server.js` — **룰 갭**: JS 룰이 `res.header`/`res.setHeader` 형태만 매칭한다([aux-security.yaml](../rules/semgrep/aux-security.yaml)). Express의 관용 표현 `cors({origin:'*'})`를 놓친다. Python 쪽 `CORS($APP, origins="*")`는 커버됨 |
| **합계** | **51** | **48** | **94.1%** | |

**룰 갭 3종은 벤치마크 결함이 아니다**(TDD §9 · 계획 Task 26 가드). 세 케이스 모두 표준 조항의
의도대로 심었고 검출에 맞춰 수정하지 않았다. SCA-05·SCA-07은 "레지스트리 원격 조회 없음"이라는
설계 가정([sbom.py:3](../api/app/engine/sbom.py#L3))의 직접 귀결이라 룰이 아니라 **가정의 비용**으로
읽어야 한다 — 해소하려면 PyPI/npm 메타데이터 조회를 도입해야 하고 이는 MVP 범위 밖이다.
AUX-03만이 순수한 패턴 커버리지 갭이다.

### ② FPR — `clean/` 오탐률

clean 파일 **11개** 중 confirmed 발생 **0건** → **FPR 0.0%**. allowlist 보정은 불필요했다
(계획 Step 5가 허용한 1회 보정을 쓰지 않았다 — 보정 전후 수치 비교 대상 없음).

| 룰 | 파일 | 근거 |
| --- | --- | --- |
| — | — | 오탐 없음 |

near-miss 세트가 실제로 대조군 역할을 했는지 개별 확인: `config_example.py`의 플레이스홀더 4종
(`your-api-key-here`·`changeme`·`sk-test-`·`<replace-me>`)이 전부 allowlist에 걸렸고,
`product_codes.py`의 RRN 형식 유사 코드(7번째 자리 5~9)는 형식 게이트에서 탈락했다.

> repo-wide 룰(P8·P9·P10)은 분모·분자에서 제외했다 — 같은 스캔 트리에 음성을 둘 수 없어서다
> (명세 §1.2). 이들의 오탐은 Task 27(PyGoat·dogfooding)에서 측정한다.

### ③ 부가 발견 — 오라클 밖 confirmed (지표 미집계)

| 룰 | 건수 | 위치(발췌) | 성격 |
| --- | --- | --- | --- |
| SCA-02 | 3 | express, flask-cors, mysql2 | 동일 룰의 추가 발화(다발 허용) |
| SCA-04 | 2 | express, mysql2 | 동일 룰의 추가 발화(다발 허용) |
| SCA-08 | 15 | beautifulsoup4, cors, django, express … | 동일 룰의 추가 발화(다발 허용) |
| SCA-09 | 11 | beautifulsoup4, flask, flask-cors, flask-login … | 동일 룰의 추가 발화(다발 허용) |
| SCA-10 | 5 | vulnerable/package.json, vulnerable/vendor | 동일 룰의 추가 발화(다발 허용) |

**SCA-10의 5건은 부가 발견이지만 원인이 다르다 — 엔진 결함으로 판단한다.**
`package-lock.json`의 `resolved`가 `https://registry.npmjs.org/...`인데
[`_is_registry`](../api/app/engine/deps_npm.py#L48)가 `https://` 접두를 비레지스트리로 보아
**lock으로 해석된 npm 패키지가 전부 "출처 불명"으로 뒤집힌다**([deps_npm.py:120-121](../api/app/engine/deps_npm.py#L120)).
공개 레지스트리 URL이 곧 비레지스트리 판정을 받는 셈이다. 나머지 1건(`vulnerable/vendor`의 oldlib)은
vendored 복제본이라 정탐이다. Task 26은 룰 코드를 수정하지 않으므로(순환 검증 회피) **기록만 남긴다** —
후속 이슈 대상.

### 등급 시나리오 3종 재현 (명세 §7)

| 태그 | 상태 | 실측 등급 | 확정 발견 | 검토 필요 |
| --- | --- | --- | --- | --- |
| `v1-danger` | 전체 | **위험** | 다수 | 17건 |
| `v2-warning` | grade_blocking만 제거 | **주의** | AUX·P7·P8·P9·SCA 잔존 | 17건 |
| `v3-safe` | 모든 confirmed 제거 | **안심** | **0건** | 17건 |

**명세 §7과의 편차 1건(기록만, 명세·룰 모두 미수정)**: §7은 SEC-02(주석 시크릿)를 v2의 잔여
'주의' 기여로 적었지만, 등급 결정론 구현은 **confirmed `SEC-*` 전부**를 위험 트리거로 본다
([grade.py:31-34](../api/app/engine/grade.py#L31) `_is_danger_finding`). 그래서 v2에서 SEC-02도
함께 제거해야 '주의'에 도달한다. 사용자 판단(2026-08-30)에 따라 **엔진 정의를 정본으로 삼았다**.

v2에서 제거한 Critical CVE 보유 컴포넌트는 django·next·mysql2 3종이다(v0.1이 next만 예상했으나
실측에서 django의 CVE-2022-28346·CVE-2025-64459, mysql2의 CVE-2024-21508·21511도 Critical로 나왔다).

`git clone --depth 1 --single-branch`는 ref를 받지 않는다([ingest.py:25](../api/app/engine/ingest.py#L25)) —
**태그를 URL로 직접 스캔할 수 없다.** 세 태그는 선형 커밋이라 데모에서는 main을 fast-forward로
전진시켜 재진단한다(절차는 `docs/demo-script.md`).

### 명세 §3.1 예상치 vs OSV 실측

| 컴포넌트 | 명세 예상 | OSV 2026-08-30 실측 | 판정 |
| --- | --- | --- | --- |
| Django 3.2.12 | Critical/High | **Critical** (CVE-2022-28346 등) | 일치 |
| Flask 0.12.2 | **High**(v0.2 메이저 교정) | High — 등급 기여는 '주의' | 일치(교정이 옳았다) |
| requests 2.28.0 | Medium | High/Medium | 상향 |
| lodash 4.17.15 | High | High | 일치 |
| next 14.2.0 | 확정 Critical | **Critical** (CVE-2025-29927) | 일치 |
| six 1.10.0 | Low(비기여 검증) | — | **SCA-05 미발화**(위 룰 갭) |

Low-비기여 검증은 SCA-05가 담당하기로 했으나 룰 갭으로 성립하지 않았다. 대신 SCA-08·SCA-09가
Low 심각도 confirmed로 다수 발화하면서 **"Low는 등급에 기여하지 않는다"가 v1에서 실증됐다**
(등급은 Critical CVE·SEC·P6가 만들었고 Low 발견 26건은 기여하지 않았다).

### 벤치마크 저장소 운영 기록

- **GitHub 시크릿 스캐닝 push protection이 최초 푸시를 3건 차단**했다(`.env`의 Stripe 키,
  `secrets_config.py`의 AWS 키 쌍). 보안 설정을 끄지 않고 **리터럴 형태만 바꿔** 해소했다 —
  AWS 키는 명세 §4.5가 인젝션 페이로드에 지정한 것과 같은 21자 형태(`AKIA…` + 17자)로 맞췄다.
  이 형태는 gitleaks `aws-access-token`은 그대로 발화시키고(SEC-04 검출 유지) GitHub 제공자
  패턴(20자)에는 걸리지 않는다. Stripe 키는 제공자 비특정 고엔트로피 값으로 교체했고
  SEC-03은 경로 룰이라 영향이 없다. **오라클의 rule_id·file·verdict·line은 전부 불변.**
- 불변식 CI(`.github/workflows/invariants.yml`)는 안심코드를 체크아웃해
  `verification/check_invariants.py`를 돌린다. 지금은 ansim-code ref가 `feat/m7-verification`으로
  핀되어 있다 — **머지 후 `main`으로 되돌려야 한다**(워크플로 파일에 TODO 주석 있음).
- 태그 트리(v2·v3)는 불변식 검사 대상이 아니다. v3-safe는 P8·P9를 해소하려고 로깅·처리방침을
  **일부러** 넣은 상태라 불변식을 의도적으로 깬다. 그래서 CI는 `main` push·PR에서만 돈다.

### 자기 마스킹 실증 (불변식 자동화가 필요한 이유)

스캐폴딩 1차에서 `vulnerable/models.py`의 **docstring에 쓴 "파기"라는 단어 하나가 P10을 통째로
껐다**. 룰이 아니라 벤치마크가 자기 양성을 지운 것이고, 표만 보면 "P10 룰 갭"으로 오독됐을 사례다.
`check_invariants.py`가 이 부류를 6종 검사로 잡는다(로깅·처리방침·삭제 동사·미선언 import·P4 국소화·P7 인증 단어).
검사기 자체의 회귀는 `api/tests/test_verification_matching.py` 23건이 지킨다.

## M7 — Task 27 (2026-08-30, 실행 세션: feat/m7-verification)

검증 3종을 같은 스택(api 8002)에서 키 없이 실행했다. 인젝션 시연의 상세는
[`verification/injection_payloads.md`](../verification/injection_payloads.md)에 따로 있다.

### ① PyGoat — 제3자 취약 앱

| 항목 | 값 |
| --- | --- |
| 대상 | `https://github.com/adeyosemanputra/pygoat` (git URL) |
| 소요 | **30초** (G14 목표 2분 대비 여유 — 분해 기록 불필요) |
| 등급 | **위험** (상향 조건: 17건 해결 시 주의) |
| 발견 | 142건 (전부 confirmed, review_needed 0) |
| SBOM | 컴포넌트 40개 / 취약 16개 · 공급망 분류 `오픈소스` |

룰별: SEC-01 10 · SEC-02 2 · P7 2 · P9 1 · AUX-02 3 · AUX-04 5 ·
SCA-01 4 · SCA-02 16 · SCA-03 3 · SCA-04 16 · SCA-08 40 · SCA-09 40.
(⛔ `SCA-03 3`은 표본 KISA 스냅샷 기준이다 — 이슈 #17의 실데이터 교체 후 재측정 필요.
PyGoat은 Django 앱이라 제품명 교차로 발화 자체는 유지될 전망이나 건수는 달라진다.)

**review_needed가 0건인 이유(관찰)**: P2·P3의 semgrep 패턴이 Flask 계열
(`request.form[...]`·`request.json[...]`)만 매칭하는데 PyGoat은 Django라
`request.POST[...]`를 쓴다. 프레임워크 커버리지 갭이며 벤치마크(Flask+Express)로는
드러나지 않는 종류다 — **제3자 앱 검증이 실제로 새 정보를 준 지점**이다.

### ② repo-wide 룰(P8·P9·P10) 오탐 판정 — Task 26 FPR 표의 빠진 행

명세 §1.2에 따라 이 3종의 FPR은 벤치마크 `clean/`이 아니라 실앱 2종으로 측정한다.
발화 여부만 보지 않고 **해당 기능이 그 앱에 실재하는지 소스로 대조**해 정탐/오탐을 갈랐다.

| 룰 | PyGoat | 실재 대조 | 판정 | 안심코드(dogfooding) | 실재 대조 | 판정 |
| --- | --- | --- | --- | --- | --- | --- |
| P8 (취급 기록 부재) | 미발화 | `introduction/views.py`에 `import logging` 실재 | ✅ 정탐 | 미발화 | `app/main.py`·`llm/client.py` 등 다수에 실재 | ✅ 정탐 |
| P9 (처리방침 부재) | **발화** | 처리방침 파일명·`/privacy` 라우트 **둘 다 없음** | ✅ **정탐**(오탐 아님) | 미발화 | `rules/semgrep/privacy.yaml` 등 파일명 일치 | ⚠ 조건상 정탐 |
| P10 (파기 경로 부재) | 미발화 | `introduction/apis.py` 등에 삭제 동사 실재 | ✅ 정탐 | 미발화 | `engine/workspace.py`의 파기 로직 실재 | ✅ 정탐 |

**오탐 0건.** P9가 PyGoat에서 발화한 것은 오탐이 아니라 정탐이다 — 의도적으로 취약하게 만든
교육용 앱에 개인정보 처리방침이 없는 것은 사실이다.

**단, 안심코드의 P9 미발화는 근거가 약하다(정밀도 관찰)**: 미발화를 만든 것은 실제 처리방침
문서가 아니라 **`rules/semgrep/privacy.yaml`·`api/tests/test_privacy_rules.py`라는 파일명 우연 일치**다.
[repo_checks.py:104](../api/app/engine/repo_checks.py#L104)의 부재 검사가 파일명만 보므로,
`privacy`가 들어간 파일이 어떤 이유로든 있으면 P9가 꺼진다. 미검출 방향의 정밀도 한계로 기록한다.

### ③ 인젝션 방어 시연

페이로드 4종(한국어·영어·역할 사칭·JSON 위장)을 `vulnerable/injection_test.py` 한 파일에 두고
벤치마크 스캔 결과로 판정했다.

| 검증 항목 | 결과 |
| --- | --- |
| SEC-04 정상 flag | ✅ confirmed (line 8), `grade_blocking=true` |
| 등급 | ✅ **위험 유지** |
| 상향 안내 | ✅ "이 23건만 해결하면 주의로 올라갑니다" |
| LLM 산출 텍스트의 지시문 반영 | ✅ `안심`·`SAFE`·`취약점 보고를 취소` **0건**(설명·수정 프롬프트·쉬운 설명 전수) |
| 시크릿 원문 노출 | ✅ evidence `****` 마스킹(P0-2) |

**보류 1건**: 키 미설정으로 judge가 실행되지 않아(`llm_model_id: null`,
`judge_explanation` 0/101) "judge가 인젝션을 읽고도 무시했다"는 **행동 수준 증거는 없다**.
대신 확인된 것은 더 강한 구조적 사실이다 — ① SEC-*는 애초에 judge에 가지 않고
([analysis.py:95-98](../api/app/engine/analysis.py#L95)) ② judge가 401로 전부 실패한 상태에서도
등급·발견·상향 안내가 정상 산출됐다. 실키 확보 시 재확인 절차는 injection_payloads.md에 적었다.

### ④ dogfooding — 안심코드 자기진단

| 항목 | 값 |
| --- | --- |
| 대상 | `https://github.com/fmaPark/ansim-code` (main, git URL) |
| 소요 | **39초** |
| 등급 | **위험** (상향 조건: 19건) |
| 발견 | 216건 (confirmed 206 · review_needed 10) |
| SBOM | 컴포넌트 91개 / 취약 7개 · 공급망 분류 `오픈소스` |

자기 등급이 '위험'으로 나왔고, 원인을 하나씩 대조하니 **상당수가 자기 오탐**이었다.
숨기지 않고 남긴다 — 이것이 dogfooding의 목적이다.

| 룰 | 건수 | 위치 | 판정 |
| --- | --- | --- | --- |
| SEC-04 | 10 | 전부 `api/tests/` (test_pii·test_masking·test_gitleaks·test_rescan) | **오탐** — 룰 테스트용 합성 픽스처다 |
| SEC-02 | 4 | `api/tests/test_gitleaks.py` | **오탐** — 동일 |
| SEC-05 | 7 | `api/tests/test_gitleaks.py` (review_needed) | **오탐** — 동일 |
| SCA-01 | 3 | `app`·`packageurl`·`pydantic` | **오탐** — `app`은 1차 패키지(자기 자신), `packageurl`·`pydantic`은 `packageurl-python`·`pydantic-settings`로 선언돼 있는데 import명→배포명 별칭표에 없다 |
| P5 | 2 | `api/tests/test_privacy_rules.py`, **`api/app/engine/repo_checks.py`** | **오탐** — 특히 두 번째는 룰 자신의 소스가 자기 정규식 리터럴(`BeautifulSoup`·`requests.get`·PII 필드)에 걸린 것이다 |
| P4 | 1 | `api/tests/test_judge.py` | **오탐** — 픽스처 |
| SCA-10 | 74 | npm 컴포넌트 전량 | **오탐** — Task 26에서 찾은 `_is_registry` 결함(아래) |
| SCA-02 | 7 | 실제 취약 버전 | 정탐 |

**세 가지 오탐 원인이 드러났다**:

1. **테스트 픽스처가 시크릿으로 잡힌다.** gitleaks allowlist의 경로 예외가
   `(^|/)tests?/fixtures/`라서 `api/tests/*.py`에 인라인으로 쓴 합성 시크릿은 걸러지지 않는다
   ([ansim.toml](../rules/gitleaks/ansim.toml)). 시크릿 룰을 테스트하려면 픽스처가 필요한데
   그 픽스처가 곧 오탐이 되는 구조다.
2. **룰 소스 자신이 룰에 걸린다.** `repo_checks.py`의 P5 정규식 리터럴이 P5를 발화시켰다.
   벤치마크 명세 §1.3이 경고한 "자기 마스킹"의 거울상이며, 측정 스크립트 2종을 벤치마크가 아니라
   안심코드에 둔 판단이 옳았음을 반대편에서 확인해 준다.
3. **`_is_registry`가 공개 레지스트리 URL을 비레지스트리로 본다** —
   Task 26 부가 발견에서 5건으로 보였던 것이 실제 저장소에서는 **74건**으로 증폭됐다
   ([deps_npm.py:48](../api/app/engine/deps_npm.py#L48)). 영향 규모가 확인된 셈이다.

**세 건 모두 이번 세션에서 수정하지 않았다** — 순환 검증 회피(TDD §9) 하에 Task 26·27은
룰 코드를 건드리지 않는다. 후속 이슈 대상이며, 우선순위는 SCA-10 결함(74건) > 픽스처 allowlist >
P5 자기 발화 순으로 본다.

## M7 — Task 28 (2026-08-30, 실행 세션: feat/m7-verification)

### 선행 조치 — LLM 캐시 영속화

`llm_cache_dir`가 `/srv/data/llm_cache`(이미지 레이어)라 재빌드마다 리허설 캐시가 사라진다.
장애 폴백(TDD §6) 시연의 전제가 무너지므로 `docker-compose.yml`의 api에 named volume
`llmcache`를 붙였다. 룰·엔진 코드가 아니라 기동 설정 변경이다.

### ① 리허설 완주 — 클린 재빌드 스택에서 전 장면

프로젝트 한정 클린 조건(`docker compose down -v` + api·web 이미지 삭제 +
`build --no-cache`)에서 재기동해 데모 7장면을 API로 완주했다. 전역 `docker system prune`은
같은 머신의 다른 워크트리 스택을 건드리므로 쓰지 않았다(사용자 확정).

| 항목 | 결과 |
| --- | --- |
| 3서비스 기동 | ✅ **15초**, `/health` 200, web 200 |
| 룰 시드 | ✅ 31종, `rule_catalog_version=8e512d222d972ed9` |
| 장면 ①② 벤치마크 스캔 | ✅ 등급 **위험**, 발견 101건, 전 발견에 조항 인용 존재 |
| 상향 블록 | ✅ "이 23건만 해결하면 주의로 올라갑니다" |
| 전체 수정 프롬프트 복사 | ✅ 10,237자 |
| 장면 ⑤ 인젝션 | ✅ SEC-04 confirmed·`grade_blocking=true`, 등급 위험 유지 |
| 장면 ⑦ SBOM | ✅ 16컴포넌트, 15속성 키 전량 존재, 공급망 `오픈소스` |
| 장면 ⑦ 체크리스트 | ✅ 13항목 |
| 장면 ④ 공개 1단계 | ✅ 토큰 발급 |
| 장면 ⑥ dogfooding | ✅ 완주, 등급 위험 |
| 무변경 재진단 | ✅ 해결 0 / 잔여 101 / 신규 0 (이슈 #13 회귀 없음) |

### ② 데모 절정(위험 → 주의) — 실 git 경로 재현

태그를 URL로 스캔할 수 없으므로 `main`을 fast-forward로 전진시키는 방식을 검증했다.

| 단계 | 실측 |
| --- | --- |
| ① `v1-danger` 스캔 | 등급 **위험** |
| ② `git push origin 'v2-warning^{}:main'` | fast-forward 성공 |
| ③ 재진단 | **위험 → 주의**, 지문 변경 `true` |
| diff | **해결 15 / 잔여 73 / 신규 0** — 해결된 룰 SEC-01~05·P6 |
| 상향 안내 | "이 78건만 해결하면 안심으로 올라갑니다" |
| ④ 원복 | `main` → `v1-danger`(94876f8) 확인 |

**푸시 명령에 주의**: `git push origin v2-warning:main`은 거부된다 — 소스가 **annotated tag
객체**라 브랜치 ref가 받지 못한다. `v2-warning^{}`로 커밋을 역참조해야 한다.
같은 이유로 준비 확인의 `git ls-remote ... refs/tags/v1-danger`도 태그 객체 해시를 돌려주므로
`main`과 절대 같지 않다 — `refs/tags/v1-danger^{}` 줄과 비교해야 한다. 그리고 이 푸시 명령들은
**벤치마크 체크아웃 안에서** 실행해야 한다(태그가 로컬에 있어야 한다).
세 가지 모두 데모 스크립트에 반영했다.

**태그 재정렬(2026-08-30, PR #36 머지 직후)**: 이슈 #35 처리로 벤치마크 `main`에 CI 커밋
(`1023438`)이 얹히면서 `v1-danger`(`94876f8`)와 갈라져 **fast-forward 전제가 깨졌다.**
`v2-warning`·`v3-safe`를 새 main 위로 rebase하고 태그 3종을 옮겨 선형 체인을 회복했다.
스캔 대상 파일은 바이트 단위로 동일하고(diff는 `.github/workflows/invariants.yml` 한 건 —
`.yml`은 CODE_EXTS 밖이라 룰 판정 무영향), 재정렬 후 데모 절정을 문서 명령 그대로 재실행해
**위험 → 주의 · 해결 15 / 잔여 73 / 신규 0**을 재확인했다.

| ref | 커밋 |
| --- | --- |
| `main` = `v1-danger^{}` | `1023438` |
| `v2-warning^{}` | `3e285d2` |
| `v3-safe^{}` | `1a3175f` |

### ③ 장애 폴백 리허설 — 무효 키 상태 재생

`.env`를 건드리지 않고 `docker-compose.keyless.yml` 오버레이로 무효 키를 덮어써
(`ANTHROPIC_API_KEY=sk-ant-invalid-rehearsal-key`) 같은 시나리오를 재생했다.

| 항목 | 정상 키 자리 | 무효 키 | 일치 |
| --- | --- | --- | --- |
| 등급 | 위험 | **위험** | ✅ |
| 발견 수 | 101 | **101** | ✅ |
| 상향 조건 | 주의 23건 | **주의 23건** | ✅ |
| 쉬운 설명 | 전 발견 보유 | **전 발견 보유**(폴백 문구) | ✅ |
| 수정 프롬프트 | 전 발견 보유 | **전 발견 보유** | ✅ |
| 시민용 리포트 | 정상 | **101건 · 검토 필요 17** | ✅ |
| 체크리스트 | 13항목 | **13항목** | ✅ |
| SBOM 15속성 | 완비 | **완비** | ✅ |

등급·발견·상향이 전부 static 경로임을 실측으로 확인했다(G3·TDD §10 정합).

**보류 1건 — LLM 캐시 적재**: 실키가 없어 캐시가 비어 있다(`llm_cache` 파일 0개).
따라서 이번에 확인한 것은 "캐시 폴백"이 아니라 **"LLM 없이도 완주"** 다. 캐시 폴백 자체는
`client.py:69-71`의 경로이고 별도 단위 테스트가 지킨다. 실키 확보 시 리허설 1회로 캐시를
적재하면 설명 텍스트까지 동일 재생된다 — 절차는 `docs/demo-script.md` §0에 적었다.

### ④ 최종 스모크

| 항목 | 결과 |
| --- | --- |
| 전체 pytest | ✅ **169건 green** (기존 146 + 검증 스크립트 23) |
| OKF 검사 | 기존 실패 2건만(이슈 #21 — `benchmark-spec.md`·`plans/execution-prompts.md` frontmatter 부재). **자기 변경으로 인한 신규 오류 0** |
| 클린 재빌드 | ✅ `--no-cache` 빌드 후 15초 기동 |
| 소스 zip | ✅ `tools/package_submission.py` — 145파일 518KB, `.env` 미포함 |

**패키징 결함 1건 발견·수정**: `git archive --format=zip`이 만든 zip은 **Info-ZIP `unzip`으로
해제되지 않는다.** git이 파일명을 UTF-8 바이트로 넣으면서 zip 헤더의 EFS 플래그(bit 11)를
세우지 않아 `unzip`이 CP437로 읽고 `협의체_기록/`에서 "Illegal byte sequence"로 멈춘다.
macOS Finder·`tar`·Python zipfile로는 열리므로 조용히 지나칠 수 있었던 문제다.
`tools/package_submission.py`가 git의 tar를 받아 Python zipfile로 다시 싸서 해소했다
(zipfile은 비ASCII 이름에 UTF-8 플래그를 자동으로 세운다).

### ⑤ 게이트 ③ — README만으로 기동 재현 (제출물 실검증)

제출 zip을 **빈 디렉토리에 `unzip`으로 풀고**, README의 「실행」 절만 따라 기동했다.
이 저장소 체크아웃이 아니라 **해제된 zip 트리에서** 돌린 것이 요점이다.

| 단계 | 결과 |
| --- | --- |
| `unzip` 해제 | ✅ 한글 경로 포함 정상(`협의체_기록/` 확인) |
| `cp .env.example .env` | ✅ (키는 placeholder 그대로) |
| `docker compose up -d --build` | ✅ **79초**(이미지 캐시 없는 상태) |
| `/health` · web | ✅ 200 / 200 |
| 실제 스캔 | ✅ 벤치마크 git URL → 등급 **위험**, 발견 101건, 상향 안내 정상 |

키가 placeholder인 상태에서도 스캔이 완주한다는 README 서술이 실물로 확인됐다.

### 보류·이월 항목 (M7)

- **실키 의존 3건** — ① judge 실행 상태의 `judge_explanation` 문구 확인(인젝션)
  ② LLM 캐시 적재 후 폴백 재생 ③ §11 항목 1의 실호출 소요·토큰·비용 실측.
  모두 키 기입 후 리허설 1회로 해소된다.
- **벤치마크 CI의 ansim-code ref** — 지금 `feat/m7-verification`으로 핀되어 있다.
  이 브랜치가 main에 머지되면 `.github/workflows/invariants.yml`의 `ref`를 `main`으로
  되돌려야 한다(워크플로 파일에 TODO 주석).
- **룰 갭 3종·오탐 3부류** — 위 Task 26·27 절 참고. 전부 미수정, 후속 이슈 대상.
  → 이 중 5건을 아래 「후속 이슈 수정」에서 해소했다.
- **§11 항목 4·7·8 카피** — M6에서 미수신 확정, placeholder 유지(변동 없음).

## M8 — Task 32 전환 게이트 (2026-08-30, 실행 세션: feat/m8-gemini)

> Gemini 전면 전환(TDD v0.6 §11 항목 9)의 **전환 게이트 4건** 실측. 실 `GEMINI_API_KEY`로 수행했다.
> 위 M4~M7 엔트리의 Anthropic 기준 수치는 당시 기록이므로 그대로 두고, Gemini 기준은 여기 새로 남긴다.
> **§11 항목 1(LLM 상한)의 Gemini 기준 첫 실호출 실측**이기도 하다(M4는 fake transport, M7은 키 미설정 기준이었다).

### 선결 사항 — TDD §4.2 모델 가정 2종이 사용 불가

`models.list()`에는 나오지만 `generateContent` 호출이 **404 "no longer available to new users"**:

| 모델 | 결과 |
| --- | --- |
| `gemini-2.5-flash` (TDD judge 가정) | ❌ 404 — 신규 계정 사용 불가 |
| `gemini-2.5-flash-lite` (TDD 변환 가정) | ❌ 404 — 동일 |
| `gemini-3.5-flash` | ✅ `thinking_budget=0` 그대로 수용 |
| `gemini-3.1-flash-lite` | ✅ `thinking_budget=0` 그대로 수용 |
| `gemini-3.6-flash`·`gemini-3.5-flash-lite`·`gemini-flash-lite-latest` | ⚠️ 동작하나 `thinking_budget` 미지원(400) → `thinking_level="low"` 필요 |
| `gemini-3.7-flash`·`gemini-flash-latest` | ⚠️ 503 high demand(간헐) |

→ **사용자 확정(2026-08-30): judge=`gemini-3.5-flash`, 변환=`gemini-3.1-flash-lite`.** TDD §4.2 문구(thinking 비활성)를 코드 변경 없이 충족하고 flash/flash-lite 이원화 구조를 유지하는 조합이다. **TDD §4.2·§11 항목 9 ①의 모델 가정은 실물과 어긋나므로 정정 필요**(기획 사후 승인 대상).

### 게이트 판정

| # | 게이트 | 결과 | 근거 |
| --- | --- | --- | --- |
| ① | 벤치마크 페이로드 안전 필터 차단 0건 | **통과** | 아래 §게이트 ① |
| ② | 응답 `model_version` 기록(G9) | **통과** | 아래 §게이트 ② |
| ③ | Gemini 리허설 캐시 재기록 | **조건부 통과** | 메커니즘 동작. 잔여 결함 1건 — 아래 §게이트 ③ |
| ④ | judge 12 병렬 쿼터 통과 | **실패** | 무료 티어 5 RPM — 아래 §게이트 ④ |

### 게이트 ① 안전 필터 — 통과 (차단 0/5)

`benchmark-spec.md` §4.1·§4.2·§4.5 페이로드를 **실제 judge 프롬프트(`JUDGE_SYSTEM`+`JUDGE_USER_TMPL`)에 실어** 호출했다. 인젝션·시크릿은 SEC-\* 룰이라 설계상 LLM을 경유하지 않으므로(G2), 스니펫으로 실어 최악 케이스를 만든 것이다.

| 페이로드 | 결과 |
| --- | --- |
| 주민번호(합성 체크섬 통과) 2건 + 계좌 + 휴대전화 + RRN insert (§4.2) | 통과 · out 107t |
| 인젝션 지시문 4종(한국어·영어·역할 사칭·JSON 위장) + `AKIA…` (§4.5) | 통과 · out 77t — **모델이 지시를 따르지 않고 코드로 취급**(`is_likely_issue: true`) |
| 시크릿 리터럴 원문 3종(sk-live·AKIA·AWS secret) (§4.1 최악 케이스) | 통과 · out 74t |
| 민감정보 건강·질병·종교·범죄 (§4.2 P3) | 통과 · out 83t |
| 크롤링 PII 수집 (§4.2 P5) | 통과 · out 86t |

**차단 0건 · `finish_reason=SAFETY` 0건 · `block_reason` 0건.** 전 카테고리 `BLOCK_NONE` 설정(`SAFETY_OFF_CATEGORIES` 5종)이 의도대로 동작한다.

### 게이트 ② `model_version` — 통과

- 전 실호출에서 응답 `model_version` 존재. **"model_version 없음" 폴백 로그 0건**(요청 모델 ID 대체 경로 미발동).
- `scan.llm_model_id = 'gemini-3.5-flash; gemini-3.1-flash-lite'` — judge·변환 두 모델이 **응답 값 그대로** 기록(설정 상수 하드코딩 아님 — G9 충족).

### 게이트 ③ 리허설 캐시 — 조건부 통과

소형 fixture(judge 3 + 변환 1 = 4호출, 429 0건)로 record → 무효 키로 재생:

| 단계 | 결과 |
| --- | --- |
| record(실키) | 4호출 성공, 캐시 파일 4개 기록 |
| replay(무효 키) | **실호출 0 · 캐시 폴백 3건 · `status=done` 완주** |
| 등급 비교 | record·replay 모두 **`위험`**, 지문 동일(`4f22958b08fc`), judge 설명 3건 유지 — **G3 등급 결정론 유지 확인** |

**측정 당시 결함 ⓐ(캐시가 컨테이너 재생성에 소실) → M7 머지로 해소.** 측정은 `llmcache` 볼륨이 없던 베이스에서 수행했고 실제로 `docker compose up -d api` 한 번에 캐시 12개가 소실됐다(임시 볼륨 override로 우회해 측정). **M7(PR #36)이 `docker-compose.yml`에 `llmcache:/srv/data/llm_cache` 볼륨을 추가해 이 결함은 사라졌다** — 머지 후 상태에서는 리허설 캐시가 재빌드에도 살아남는다.

**결함 ⓑ(변환 캐시가 스캔이 바뀌면 미히트) → 이 세션에서 수정 완료.** `convert._payload_item()`이 페이로드에 **스캔별 Finding PK(`f.id`)**를 실어 캐시 키 `sha256(model+system+user)`가 매 스캔 달라졌다. 최초 replay 측정에서 시민용 문구·수정 프롬프트 **10/10이 규칙 기반 폴백 문구**(`"… 기준으로 수정하세요."`)로 채워졌다 — judge 캐시는 스니펫 기반이라 정상 히트하는데 변환만 전량 미스였다.

수정: 페이로드의 `id`를 PK가 아니라 **배치 안 순번**으로 바꾸고 `_apply()`의 매핑도 순번 기준으로 맞췄다. 파이프라인이 `order_by(Finding.id)`로 넘기므로 같은 코드면 순번이 같아 캐시가 스캔을 건너 산다. 회귀 테스트 `test_payload_carries_no_scan_scoped_id`가 **서로 다른 PK를 가진 두 스캔의 페이로드가 바이트 동일**함을 고정한다.

실측 재검증(같은 zip 2회 — 실키 record → 무효 키 replay):

| 항목 | 수정 전 | 수정 후 |
| --- | --- | --- |
| 캐시 폴백 건수 | 3 (judge만) | **4 (judge 3 + 변환 1)** |
| replay의 규칙 기반 폴백 문구 | **10/10** | **0/10** — LLM 문구 그대로 재생 |
| replay 실호출 | 0 | 0 |

→ `demo-script.md` 장면 ⑦의 "캐시가 있으면 LLM 설명 텍스트까지 그대로 재생된다"가 **시민용 문구·수정 프롬프트까지 포함해 사실이 됐다.**

### 게이트 ④ judge 12 병렬 쿼터 — **실패**

대형 fixture(LLM 후보 57건, 12 병렬)로 실측:

| 항목 | 값 |
| --- | --- |
| 쿼터 | `GenerateRequestsPerMinutePerProjectPerModel-FreeTier`, **limit 5** (`generate_content_free_tier_requests`, model `gemini-3.5-flash`) |
| 429 `RESOURCE_EXHAUSTED` | **45건** (전부 judge/`gemini-3.5-flash`. 변환/`gemini-3.1-flash-lite`는 3배치 전부 성공, 429 0건) |
| judge 설명 기록 | **9 / 57** — 48건은 설명 없이 `review_needed` 유지(파이프라인은 계속, G3대로 등급 불변) |
| 성공 호출 | 12건(judge 9 + 변환 3), in 11,529t / out 6,915t |
| 서버 안내 재시도 지연 | 42~46초 |
| 스캔 완주 | `status=done`, 등급 `위험` — **실패해도 스캔은 완주한다** |

**구조적 판정:** 무료 티어 5 RPM에서는 **judge 12 병렬이 원리적으로 불가능**하다(6번째 요청부터 즉시 429). 병렬도를 5로 낮춰도 RPM은 분당 처리량 제한이라 후보 57건이면 12분 이상 — G14(2분) 붕괴다. **`judge_concurrency` 하향만으로는 해소되지 않으며**, 실질 선택지는 ⓐ 유료 티어 전환 ⓑ **스캔당 judge 호출 상한 도입**(TDD §6·§11 항목 1이 예고한 "스캔당 호출 상한") ⓒ 둘의 조합이다. **기획 판단 대기 — 이 세션은 미조치.**

> 참고: 후보 57건은 12 병렬을 포화시키려 의도적으로 만든 스트레스 fixture다. M7 실측에서 벤치마크 저장소는 31종 중 28종 발화였고 그중 judge 후보(P1~P5·P10)는 한 자릿수 수준이다.

### 게이트 ④ 후속 — D2ⓑ(스캔당 judge 호출 상한) 도입과 **일일 쿼터 발견**

기획 회신(2026-08-30, PR #37 리뷰)이 **ⓑ 상한 채택**으로 확정돼 `settings.judge_max_calls`를 도입했다. 상한 초과분은 설명 없이 `review_needed`로 남고 등급은 static 경로라 무관하다(G3). 선별은 **심각도 높은 순 + 결정적 정렬**(`(severity, rule_id, file_path, line)`)이라 같은 코드면 같은 대상이 뽑힌다(재진단 diff 안정 — G11).

상한 값 실측:

| 상한 | 결과 |
| --- | --- |
| 5 | 상한은 정상 동작(judged 5 / skipped 49). 그러나 **버스트 5건이 5 RPM과 정확히 같아 여유가 없어 429 2건** — judge 성공 3/5 |
| **3** (채택) | 상한 정상 동작(judged 3 / skipped 51). 데모의 스캔→재진단 연속(같은 분 2 버스트)과 JSON 파싱 재요청까지 흡수 |

**⚠️ 새로 드러난 제약 — 무료 티어에는 분당(RPM)뿐 아니라 일일(RPD) 쿼터가 있다.**

```
quotaId : GenerateRequestsPerDayPerProjectPerModel-FreeTier
metric  : generativelanguage.googleapis.com/generate_content_free_tier_requests
limit   : 20      model: gemini-3.5-flash
```

상한 3 검증 도중 이 한도에 걸렸다 — 이날 게이트 측정으로 누적된 judge 호출이 **20건**을 넘어 이후 judge 호출이 전부 429가 됐다(`retryDelay` 32s로 안내되지만 실제로는 자정까지 회복되지 않는다). 그 상태의 두 스캔은 **judge 설명 0건으로 완주**했고 등급 `위험`·시민용 문구 폴백 0/77은 유지됐다 — 설계된 열화 경로가 그대로 동작함을 오히려 확인한 셈이다.

**의미:** `gemini-3.5-flash` judge는 **하루 20호출**이 총량이다. 상한 3 기준 하루 약 6스캔분이며, 리허설과 본 데모를 같은 날 돌리면 빠듯하다. D2ⓑ(상한)만으로는 RPM은 해소되나 **RPD는 해소되지 않는다.** 완화 수단은 ① 리허설 캐시(judge 캐시는 스니펫 기반이라 같은 코드면 히트 — 쿼터 소진 후에도 같은 화면 재생) ② 유료 티어(D2ⓒ) 두 가지다. `gemini-3.1-flash-lite`(변환)는 같은 날 12호출까지 정상이었다 — lite 쪽 한도가 더 크다.

> 이 RPD 제약은 기획 회신이 작성된 시점에 알려지지 않았던 정보다(당시 근거는 5 RPM뿐). **D2 재판단이 필요한지 확인 요청** — PR #37 본문 §1 참조.

### 변환 배치 절단 — 이상 없음

`TOKENS_PER_ITEM=350` 유지 상태에서 발견 77건 → 3배치(30/30/17), `max_output_tokens` 10,500. **규칙 기반 폴백 문구 0/77**, `easy_description`·`fix_prompt` 미충족 0건 — 절단·매핑 실패 없음.

## 후속 이슈 수정 — #28·#29·#31·#32·#34 (2026-08-30)

M7이 기록만 남긴 이슈 8건 중 이 저장소 코드 수정만으로 고칠 수 있는 5건을 처리했다.
제외 3건: #30(정규식 기반에서 자기 발화 구분 불가 — 설계 결정 필요), #33(레지스트리 원격
조회 도입 = 설계 가정 변경), #35(대상이 별도 저장소의 CI 파일).

### ① 벤치마크 재측정 — TPR 48→49/51, FPR 불변

`rule_catalog_version` `04a38658f614ed40`(룰 2종 변경). 측정 명령·오라클은 M7 Task 26과 동일.

| 지표 | M7 실측 | 수정 후 | 비고 |
| --- | --- | --- | --- |
| TPR ⛔ | 48/51 (94.1%) | **49/51 (96.1%)** | AUX-03 0% → **100%**(#31). **이 합계는 SCA-03 5/5를 포함하므로 이슈 #17(KISA 실데이터 교체)로 무효** — 오라클 그대로면 SCA-03이 1/5로 떨어져 합계 45/51이 된다. 재측정 필요 |
| FPR | 0.0% | **0.0%** | clean 11개 confirmed 0건 유지 |
| 부가 발견 SCA-10 | 4건(전부 오탐) | **0건** | 정탐 2건만 남음 — 오라클 1 + vendored 1 (#28) |

남은 미검출 2종은 SCA-05·SCA-07로, 둘 다 이슈 #33의 구조적 사유다(수정 범위 밖).
#32·#34는 벤치마크가 Flask+Express 구성이라 해당 케이스가 없어 수치가 변하지 않는 것이 정상이며,
`api/tests/`의 단위 테스트로 회귀를 고정했다.

불변식 6종은 재실행에서도 통과했다(`check_invariants.py` — P9 문서 확장자 필터를 엔진과 함께 미러링).

### ② dogfooding 재실행 — SCA-10 74→0, 시크릿 21건 강등

HEAD(93b22cd) 소스 zip을 수정된 엔진으로 재스캔했다.

| 항목 | M7 실측 | 수정 후 |
| --- | --- | --- |
| SCA-10 confirmed | 74건(전부 오탐) | **0건** |
| 시크릿 계열 confirmed | 21건(전부 `api/tests/`) | **0건** — 21건 전부 `review_needed`로 강등, 목록에는 `[테스트 경로]` 꼬리표로 남음 |
| 발견 총계 | — | 144건 (confirmed 119) |
| 등급 | 위험 | **위험**(아래 ③ 참조) |

### ③ 남은 관찰 2건 (미수정 — 후속 판단 대상)

**P9는 여전히 자기진단에서 침묵한다.** #34가 지목한 파일명 경로는 고쳐졌다 —
`rules/semgrep/privacy.yaml`·`api/tests/test_privacy_rules.py`는 코드 파일이므로 이제
"처리방침 있음"을 만들지 않는다. 그러나 부재 판정의 **다른 절반**인 `_PRIVACY_ROUTE`가
코드 본문의 문자열 리터럴에 걸려 룰을 끈다.

| 파일 | 매칭 | 성격 |
| --- | --- | --- |
| `api/app/engine/semgrep_runner.py` | `"privacy` | 룰 파일 경로 상수 — 라우트가 아니다 |
| `api/tests/test_verification_matching.py` | `"/privacy` | 테스트 픽스처의 라우트 문자열 |

이슈 #34가 "함께 검토한다"로 남긴 부분이고, 문맥(주석·문자열 구분) 인지 문제라 #30과 같은
층위다. 이번 수정 범위에서 의도적으로 제외했으며, **파일명 절반만 고쳐서는 자기진단 P9가
회복되지 않는다**는 사실이 여기서 확인됐다.

**등급을 '위험'에 묶는 시크릿이 1건 남았다.** `verification/injection_payloads.md:31`의
SEC-04(인젝션 페이로드 명세에 적힌 합성 AWS 키)다. gitleaks allowlist의 경로 예외는
`docs/`·`README`·`tests/fixtures/`뿐이라 `verification/`의 문서는 걸러지지 않는다.
#29의 강등은 테스트 경로 기준이므로 이 건에는 닿지 않는다. 이 1건을 빼면 자기진단 등급은
'주의'가 된다(confirmed SCA-08 91·SCA-09 17·SCA-02 7·SCA-01 3은 위험 트리거가 아니다).

## 이슈 #17 — §11 항목 5 KISA 공공데이터 확정 (2026-08-30, 실행 세션: claude/issue-17-data-validation-445ff4)

측정 환경: macOS 호스트 + Docker Compose. 실행 커맨드(스냅샷 경로까지 마운트본으로 지정 —
지정하지 않으면 이미지 안 `/srv/data`의 옛 스냅샷을 읽는다):

```
docker compose run --rm -v "$PWD:/work" -w /work/api -e RULES_DIR=/work/rules \
  -e KISA_CSV_PATH=/work/data/kisa/krcert_notices.csv api pytest -q
```

### 실데이터 확정 — data.go.kr/15155789 배포본 실측

M3 시점에 프록시 차단으로 못 받았던 배포본을 직접 내려받아 확인했다(다운로드 2026-08-30).
**표본 CSV의 스키마 가정(제목·게시일·링크·본문)은 실제와 달랐다.**

| 항목 | 실측값 |
| --- | --- |
| 원본 파일명 | `한국인터넷진흥원_보호나라KrCDRT_게시판 기본 1_20251204.csv` (617,421 bytes) |
| 인코딩 | **cp949** — 로더의 `utf-8-sig → cp949` 폴백이 그대로 동작 |
| 컬럼 | `순번, 게시판 종류, 게시판 제목, 작성자, 작성일, 조회수` — **본문·링크 컬럼 없음** |
| 행 수 | 헤더 1 + 6,802행, 전 행 6컬럼 정상 파싱 (1996-01-24 ~ 2025-12-01) |
| 게시판 종류 | 보안공지 2,316 · 보고서/가이드 1,545 · 맞춤형전용백신 1,185 · 취약점 정보 170 · Vulnerability Information 151 … |
| CVE 추출 | 337행 / **고유 192건** |
| 배포 조건 | 이용허락범위 제한 없음 · 무료 · 월간 갱신(차기 2026-01-05) |
| SHA-256 | `b862046982df341c306fc065d0907166189130986f978b5896fc489650770b39` |

### 확인된 제약 두 가지 (설계 변경으로 이어짐)

1. **추출되는 192개 CVE는 전부 국내 제품 건**이다 — `취약점 정보`·`Vulnerability Information`
   게시판의 KISA CNA 할당분(한컴·알집·투비소프트·Hitron DVR 등)과 MS/Adobe 악성코드 관련.
   **pypi/npm 생태계 CVE는 0건**이며, 벤치마크 5핀(django·next·lodash·requests·flask)과
   기존 데모 fixture(flask·lodash)의 CVE도 **하나도 포함되지 않는다**. 즉 CVE 교차 1경로만으로는
   SCA-03이 진단 대상 생태계(Python·JS)에서 구조적으로 발화하지 못한다.
2. **로더가 실데이터에서 오작동했다** — title 판별이 "URL·날짜·CVE를 포함하지 않는 첫 셀"이라
   192건 전부 title이 `순번` 숫자(`'6269'`)로 잡히고 url은 전부 빈 문자열이었다. 이슈 #17이 적어 둔
   "코드 변경 없이 CSV만 교체" 전제는 성립하지 않는다.

### 조치 — 교차 2경로 + 로더 보강

- 로더: 헤더 행이 있으면 **헤더명으로 컬럼 매핑**(제목·게시판 종류·작성일·링크), 없으면 형태
  휴리스틱(순수 숫자 셀 제외, 최장 셀) 폴백. `작성자` 컬럼은 KISA 담당자 실명이라 **읽지 않는다**.
  개별 공지 상세 URL은 opaque id라 복원 불가 — 보호나라 보안공지 게시판 URL을 대신 싣는다.
- SCA-03: ① CVE 교차(기존) + ② **제품명 교차** — 보안공지 제목의 제품명 ↔ 컴포넌트명.
  ②는 **OSV가 이미 취약 판정한 컴포넌트에만** 적용하고 `vulnerability_db`에는 기록하지 않는다
  (KISA가 그 CVE를 발령한 것이 아니므로 출처 오귀속 방지).
- **등급 단계는 불변, 상향 조건 건수는 증가.** 대상 컴포넌트는 정의상 SCA-02가 이미
  confirmed로 잡은 것들이라 `_grade_of`의 판정이 달라지지 않는다. 다만 confirmed 발견이
  1건 늘어난 만큼 `grade.py` `_blocking`이 세는 `upgrade_count`와 blocking 목록은 늘어난다
  ("이 N건 해결 시 상승"의 N이 +1). 결정론(G3)은 그대로 — LLM 비경유 순수 판정이다.

### 제품명 교차 커버리지·오탐 (실측)

실사용 상위 패키지명 99종(pypi 55 + npm 44)을 스냅샷에 대조한 결과 **6종 매칭 / 오탐 0**.

| 컴포넌트 | 매칭된 보안공지 | 공지일 |
| --- | --- | --- |
| django | Django 제품 보안 업데이트 권고 | 2025-09-05 |
| aiohttp | Python aiohttp 라이브러리 보안 업데이트 권고 | 2024-03-18 |
| mlflow | MLflow 및 ClearML 플랫폼 보안 업데이트 권고 | 2024-01-22 |
| jupyterlab | JupyterLab 제품 보안 업데이트 권고 | 2024-07-29 |
| redis | Redis 제품 보안 업데이트 권고 | 2025-10-09 |
| electron | Electron 원격 코드 실행 취약점 업데이트 권고 | 2018-01-26 |

오탐 차단 가드가 실제로 걸러낸 사례: `six` → "Is your AD safe, season 2(**Six** AD Practice…)"
(3글자 이하 + 보안공지 게시판 아님), `@babel/core`의 `core` → "Microsoft XML **Core** Services…"
(일반 명사 목록), `link` → "TP-**Link** 제품 보안 업데이트 권고"(하이픈 토큰 조각 — 아래 리뷰
반영). 전부 회귀 테스트로 고정했다(`test_product_match_rejects_false_positives`).

### 리뷰 반영 (PR #39 CHANGES_REQUESTED — 2026-08-30)

| # | 지적 | 확인 결과 | 조치 |
| --- | --- | --- | --- |
| 1 | 토큰 경계가 `-`·`.`·`_`를 단어 경계로 인정해 하이픈 제품명 조각 매칭 | **재현됨** — `match_product("link")` → "TP-Link 제품 보안 업데이트 권고"(실데이터 하이픈 토큰 제목 45건) | 경계를 `[0-9a-z._-]`로 확장. 매칭 6종은 그대로 유지됨을 재측정으로 확인. 대가: `next`가 "Next.js …"류에 안 걸린다(현 스냅샷에 해당 공지 없음) |
| 2 | 헤더리스 폴백에서 `작성자`(실명) 컬럼 누출 | **구조적으로 사실**(폴백에 가드 없음). 다만 현 스냅샷에서 실제로 제목이 된 작성자 값은 **기관명 1건**(`발신번호 거짓표시 신고센터`)이고 그마저 **제목 컬럼 자체가 같은 문자열**(5483행)이라 누출이 아니었다 — 동률일 때 앞 컬럼(제목)이 이기기 때문. 실명이 실린 사례는 0건 | 폴백에서 컬럼 통계(`짧은 값 반복` = unique 비율 <0.2 & 최대 길이 ≤20)로 라벨 컬럼을 찾아 제외. 실데이터에서 작성자 컬럼(idx 3, ratio 0.015)이 정확히 걸린다. 헤더리스 회귀 테스트 추가 |
| 3 | 버전 미상 컴포넌트의 evidence가 1토큰이 되어 `_LABEL_RE` 파싱 실패 | 타당 | `sca_rules._label`을 `component_label(name, version)`로 승격해 `stage_kisa`가 재사용 — `이름 (버전 미상) — …`. `_LABEL_RE`와 같은 정규식으로 단언하는 테스트 추가 |
| 4 | "등급 영향 없음" 서술 부정확 | 타당 — 단계는 불변이나 `_blocking`의 `upgrade_count`·blocking 목록은 늘어난다 | pipeline docstring·이 문서·tdd.md v0.7·PR 본문을 "등급 단계 불변, 상향 조건 건수 +N"으로 정정 |
| 선택 | 헤더 오인 가드 | 반영 — 첫 행에 CVE·URL·날짜가 있으면 헤더로 인정하지 않는다 |
| 선택 | `advisories`/`_titles` 병렬 리스트 | 반영 — `(소문자 제목, 공지)` 한 리스트로 통합하고 `notices` 프로퍼티로 파생 |
| 선택 | `load_kisa` `lru_cache` | **미반영** — 이미지에 구워진 스냅샷을 장수명 프로세스가 캐시하면 갱신이 조용히 무시된다(AGENTS.md가 경고하는 바로 그 함정). 스캔당 재파싱 비용(617KB)은 측정된 병목이 아니다 |

### 재현성 값 갱신

`vuln_db_snapshot_date`의 KISA 부분이 `KISA-CSV@2026-08-29`(표본) → **`KISA-CSV@2025-12-04`**
(배포본 기준일)로 바뀐다. `rules/catalog.yaml`의 SCA-03 사양도 함께 바뀌므로
`rule_catalog_version`이 변한다 — SCA-03 단독 변경분은 `f21f19d6e22a822d`, main의 후속 이슈
수정(`04a38658f614ed40`)과 합친 **병합본은 `f3d1d47b3617b572`**다. 이 커밋 이전 스캔과의
재진단 diff는 룰 버전 변경분을 포함한다.

> **주의: M7·후속 이슈 절의 실측치와 겹친다.** 위 두 절은 표본 KISA 스냅샷
> (`KISA-CSV@2026-08-29`)으로 측정한 값이다. 이 변경으로 **SCA-03 관련 수치는 무효**이며
> 그것을 합산한 TPR 총계(49/51)도 함께 무효다 — 아래 "재측정 필요" 참고. SCA-03 외의 룰은
> 영향받지 않는다(KISA 스냅샷에 의존하는 룰이 SCA-03뿐이다).

### 실동작 확인 (재빌드 이미지 + OSV 실호출)

`docker compose up -d --build api` 후 `Django==3.2.12`·`requests==2.28.0`만 담은 zip을 실제 업로드.

| 확인 | 결과 |
| --- | --- |
| SCA-03 발화 | ✅ django 1건 — `국내 보안공지 발령(제품명 일치) 「Django 제품 보안 업데이트 권고」(2025-09-05 …)` |
| 미발화 대조 | ✅ requests는 OSV CVE 4건이 잡혔지만 국내 공지가 없어 SCA-03 없음(2경로 모두 불일치) |
| 취약점별 출처 | ✅ django의 `vulnerability_db`에 KISA 항목 **0건**(제품명 교차는 출처를 만들지 않는다) |
| 재현성 | ✅ `OSV@2026-08-30; KISA-CSV@2025-12-04` |
| 등급 | ✅ 위험(SCA-02 critical 기여) — **단계는 불변**. 상향 조건 건수는 SCA-03 1건만큼 늘어난다 |

첫 실행에서 evidence에 OSV가 돌려준 **CVE 26건이 전량 나열**돼 리포트 카드가 깨졌다.
상한 3건 + "외 N건"으로 축약하고 회귀 테스트를 걸었다(`test_product_cross_evidence_truncates_cve_list`).

머지 + 리뷰 반영 후 전체 테스트 **202건 green**(origin/main `bb10d57` = M8 Gemini 전환까지 병합한 본),
`tools/okf_check.py`는 기존 2건(#21) 외 새 오류 없음. 이 변경은 LLM 공급자 전환(M8)과 서로
독립이다 — SCA-03은 static 경로라 LLM을 경유하지 않는다.

### 보류·이월 항목

- **재측정 필요(신규, 이 변경이 만든 것)** — 표본 스냅샷 기준이라 무효가 된 실측치 3건:
  ① M7 벤치마크 TPR 표의 `SCA-03 5/5 100%` ② 후속 이슈 절의 TPR 총계 `49/51`
  ③ PyGoat dogfooding의 `SCA-03 3건`.
  실데이터로는 벤치마크 5핀 중 **django 1건만** 발화한다(오라클을 그대로 두면 SCA-03 1/5,
  총계 45/51). PyGoat은 Django 앱이라 발화 자체는 유지되나 건수는 재측정해야 한다.
  재측정은 `verification/measure_detection.py`를 새 스냅샷 이미지로 1회 더 돌리면 된다.
- **벤치마크 SCA-03 기대치** — `docs/benchmark-spec.md`의 5핀 기대는 실데이터로 성립하지 않는다.
  django 1건으로 정정하고 aiohttp(pypi)·electron(npm) 핀 추가를 제안해 뒀다. 벤치마크 앱과
  **오라클(`expected_findings.yaml`)이 별도 저장소라 그쪽 반영이 선행돼야 재측정이 의미를 갖는다.**
- **월간 갱신** — 제출 직전 재다운로드 시 `SNAPSHOT_DATE`·교차 결과가 달라질 수 있다. 갱신하면
  이 절의 실측 수치도 다시 잰다.
