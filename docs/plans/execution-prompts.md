# 안심코드 MVP — executing-plans 실행 프롬프트 모음

[mvp-implementation.md](./mvp-implementation.md)(33태스크)를 executing-plans 스킬로 구현하기 위한 세션별 프롬프트.
스킬은 계획 파일 전체를 로드하므로 **각 프롬프트가 이번 세션의 태스크 범위를 명시적으로 제한**한다. 각 프롬프트는 복사-붙여넣기로 단독 동작하도록 공통 규칙을 반복 포함한다.

## 세션 분할과 실행 순서

**기본(순차) — 7세션:**

| 세션 | 범위 | 마일스톤 | 선행 | 특이사항 |
| --- | --- | --- | --- | --- |
| S1 | Task 1–5 | M1 | 없음 | API 키 불필요 |
| S2 | Task 6–11 | M2+M3 | S1 | KISA 실데이터 확인 게이트 |
| S3 | Task 12–16 | M4 | S2 | Task 16 Step 4만 실키 필요 |
| S4 | Task 17–21 | M5 | S3 | — |
| S5 | Task 22–25 | M6 | S4 | 기획 카피 게이트, 브라우저 수동 검증 |
| S6 | Task 26–28 | M7 | S5 + **기획 벤치마크 목록**(PR #12 완료) | 별도 공개 저장소·실키 필요 |
| S7 | Task 29–33 | M8 | S6 + **PR #27(TDD v0.6) 머지 베이스** | 실 `GEMINI_API_KEY` 필요 · `ANTHROPIC_API_KEY` 불요(폐기) |

**병렬 변형(작업자·세션 여유 시):** S1 완료 후 3개 레인 동시 진행 → 레인 A: S2 그대로 / 레인 B: S3a(Task 12–14) / 레인 C: S3c(Task 23 FE 골격). A·B 병합 후 S3b(Task 15–16), 이후 S4 → S5'(Task 22·24·25 — 23 제외) → S6.
병합 순서 A → B → C 권장. 공유 접점은 `api/app/engine/pipeline.py` 연결부와 `api/app/config.py`뿐(레인 C는 `web/`만 수정) — B·C 병합 시 이 두 파일만 충돌 주의.

**베이스 브랜치:** `origin/main`(PR #3 머지 완료 — 계획 파일 포함). 각 세션은 직전 세션 브랜치가 머지된 최신 베이스에서 분기.

---

## S1 — M1 기반 구축 (Task 1–5)

```
executing-plans 스킬을 사용해 docs/plans/mvp-implementation.md 계획을 실행해줘.

이번 세션 범위: Task 1~5 (M1 기반 구축)만. 범위 밖 태스크는 절대 건드리지 말 것.
브랜치: main(PR #3 머지됨) 기준 feat/m1-foundation 분기. main 직접 작업 금지.

규칙:
- 계획의 Global Constraints(G1~G16)·각 태스크 선행 조건·DoD를 그대로 따를 것. P0 3건(G1 파기·G2 마스킹·G3 등급 결정론)은 어떤 판단보다 우선.
- 태스크별 스텝 순서(테스트 작성→실패 확인→구현→green→커밋) 엄수. 완료 스텝은 계획 문서 체크박스를 [x]로 갱신해 해당 커밋에 포함.
- 막히면(의존성·반복 실패·지시 불명확) 추측하지 말고 중단 후 질문.
- 범위 완료 시: M1 게이트(계획 '마일스톤 순서' 표 1행)를 실제 명령으로 검증하고 테스트 출력 요약과 함께 보고한 뒤 멈출 것. PR 생성은 내가 지시할 때만.

이 세션 특이사항:
- .env는 .env.example 복사만(ANTHROPIC_API_KEY 없이 기동 확인까지 — 키는 M4에서).
- Docker Desktop이 꺼져 있으면 먼저 알려줄 것.
```

## S2 — M2+M3 SBOM·취약점 대조 (Task 6–11)

```
executing-plans 스킬을 사용해 docs/plans/mvp-implementation.md 계획을 실행해줘.

이번 세션 범위: Task 6~11 (M2 SBOM 생성 + M3 취약점 대조)만. 범위 밖 태스크는 절대 건드리지 말 것.
브랜치: M1(feat/m1-foundation) 병합된 최신 베이스에서 feat/m2-m3-sbom-vuln 분기. main 직접 작업 금지.

규칙:
- 계획의 Global Constraints(G1~G16)·각 태스크 선행 조건·DoD를 그대로 따를 것. P0 3건은 어떤 판단보다 우선.
- 태스크별 스텝 순서(테스트 작성→실패 확인→구현→green→커밋) 엄수. 완료 스텝은 계획 문서 체크박스를 [x]로 갱신해 해당 커밋에 포함.
- 막히면 추측하지 말고 중단 후 질문.
- 범위 완료 시: M2·M3 게이트를 실제 명령으로 검증하고 보고한 뒤 멈출 것. PR 생성은 내가 지시할 때만.

이 세션 특이사항:
- Task 10 Step 1(KISA 실데이터 확인, §11 항목 5)에서 다운로드가 막히면 중단하지 말고 계획의 대체 경로(동일 스키마 표본 CSV)로 진행하되, 확정 실패 사실을 '실측 기록' 섹션과 보고에 남길 것.
- OSV는 단위 테스트에서 전부 모킹, 실호출은 통합 스모크 1회만.
```

## S3 — M4 룰 엔진 + LLM (Task 12–16)

```
executing-plans 스킬을 사용해 docs/plans/mvp-implementation.md 계획을 실행해줘.

이번 세션 범위: Task 12~16 (M4 룰 엔진 + LLM)만. 범위 밖 태스크는 절대 건드리지 말 것.
브랜치: M3까지 병합된 최신 베이스에서 feat/m4-rules-llm 분기. main 직접 작업 금지.

규칙:
- 계획의 Global Constraints(G1~G16)·각 태스크 선행 조건·DoD를 그대로 따를 것. 특히 G2: 시크릿 원문은 DB·로그·LLM 페이로드 어디에도 남기지 말고, SEC-* 룰은 LLM 미경유. G3: LLM 경유 발견은 항상 review_needed.
- 태스크별 스텝 순서(테스트 작성→실패 확인→구현→green→커밋) 엄수. 완료 스텝은 계획 문서 체크박스를 [x]로 갱신해 해당 커밋에 포함.
- 막히면 추측하지 말고 중단 후 질문.
- 범위 완료 시: M4 게이트를 검증하고 보고한 뒤 멈출 것. PR 생성은 내가 지시할 때만.

이 세션 특이사항:
- Task 16 Step 4(실호출 실측)만 실제 ANTHROPIC_API_KEY가 필요 — .env에 키가 없으면 그 스텝만 보류로 표시하고 나에게 키 준비를 요청(나머지는 fake/스텁으로 진행).
- 실측 결과는 docs/measurements.md와 계획 '실측 기록' 섹션에 기록(§11 항목 1·3).
- 완료 보고에 "기획 벤치마크 목록(§11 항목 2) 확정 필요 — M7 착수 전 마감" 리마인드를 포함할 것.
```

## S4 — M5 리포트·등급 (Task 17–21)

```
executing-plans 스킬을 사용해 docs/plans/mvp-implementation.md 계획을 실행해줘.

이번 세션 범위: Task 17~21 (M5 리포트·등급)만. 범위 밖 태스크는 절대 건드리지 말 것.
브랜치: M4까지 병합된 최신 베이스에서 feat/m5-report-grade 분기. main 직접 작업 금지.

규칙:
- 계획의 Global Constraints(G1~G16)·각 태스크 선행 조건·DoD를 그대로 따를 것. 특히 G3 등급 결정론: calc_grade는 static confirmed + CVE만의 순수 함수여야 하고, LLM 산출물이 입력에 들어가면 안 됨(B3 DoD 테스트로 증명).
- 태스크별 스텝 순서(테스트 작성→실패 확인→구현→green→커밋) 엄수. 완료 스텝은 계획 문서 체크박스를 [x]로 갱신해 해당 커밋에 포함.
- 막히면 추측하지 말고 중단 후 질문.
- 범위 완료 시: M5 게이트(같은 입력→같은 등급 재현 포함)를 검증하고 보고한 뒤 멈출 것. PR 생성은 내가 지시할 때만.

이 세션 특이사항:
- Task 19의 리포트 JSON 구조는 프론트(S5)와의 계약이므로 계획에 적힌 키 이름을 임의로 바꾸지 말 것. 불가피하면 계획 문서를 같이 고치고 변경 사유를 보고.
```

## S5 — M6 Frontend 통합 + 공개 플로우 (Task 22–25)

```
executing-plans 스킬을 사용해 docs/plans/mvp-implementation.md 계획을 실행해줘.

이번 세션 범위: Task 22~25 (M6 Frontend 통합 + 공개 플로우)만. 범위 밖 태스크는 절대 건드리지 말 것.
브랜치: M5까지 병합된 최신 베이스에서 feat/m6-frontend 분기. main 직접 작업 금지.

규칙:
- 계획의 Global Constraints(G1~G16)·각 태스크 선행 조건·DoD를 그대로 따를 것.
- 백엔드 태스크(22)는 테스트 우선 스텝 엄수, FE 태스크(23~25)는 계획의 수동 검증 체크리스트를 브라우저로 실제 수행하고 항목별 결과를 보고(TDD §9 수동 전략). tsc --noEmit·npm run build 클린 필수.
- 완료 스텝은 계획 문서 체크박스를 [x]로 갱신해 해당 커밋에 포함.
- 막히면 추측하지 말고 중단 후 질문.
- 범위 완료 시: M6 게이트(전 흐름 완주)를 검증하고 보고한 뒤 멈출 것. PR 생성은 내가 지시할 때만.

이 세션 특이사항:
- 기획 카피 3건(§11 항목 4·7·8) 수신 여부를 시작할 때 나에게 물을 것 — 미수신이면 계획의 placeholder 문구 그대로 구현하고 그 사실을 보고에 남김.
- Task 25 공개 플로우 실검증에는 .ansimcode를 커밋할 테스트용 공개 git 저장소가 필요 — 없으면 만들기 전에 나에게 확인.
```

## S6 — M7 검증·데모 (Task 26–28)

```
executing-plans 스킬을 사용해 docs/plans/mvp-implementation.md 계획을 실행해줘.

이번 세션 범위: Task 26~28 (M7 검증·데모)만. 범위 밖 태스크는 절대 건드리지 말 것.
브랜치: M6까지 병합된 최신 베이스에서 feat/m7-verification 분기. main 직접 작업 금지.

사양 authority: 벤치마크 취약점 목록은 docs/benchmark-spec.md(v0.3, PR #12 승인·머지)가 확정 오라클이다. **매칭·불변식·오라클 사양은 benchmark-spec §5.1(4종 키 매칭·부가발견·다발 허용)·§1.3(저장소 전체 불변식)·§5.2(오라클) > 계획 Task 26 서술** 순으로 우선한다(Task 26 Produces가 이미 이를 명시).

시작 전 게이트(나에게 먼저 확인):
1) ansim-benchmark 별도 공개 저장소를 만들 GitHub 계정/위치. (기획 목록 게이트는 PR #12 승인으로 해소됨)

규칙:
- 계획의 Global Constraints(G1~G16)·각 태스크 선행 조건·DoD를 그대로 따를 것.
- 벤치마크 목록에 룰을 맞추는 수정 금지(순환 검증 회피 — TDD §9). 표준 의도로 심은 케이스가 미검출이면 룰 갭으로 보고(임의 수정 금지). 측정 결과는 전체 31종 기준으로 docs/measurements.md에 기록.
- benchmark-spec §1.3 불변식을 verification/check_invariants.py + CI로 자동검사(WP-3). measure_detection.py는 오라클에 미기입 센티넬(TBD·line)이 남으면 fail-closed로 측정 중단(WP-4). SCA-08 package·파일키 룰의 line은 스캐폴딩 후 기입(rule_id·verdict 불변).
- 완료 스텝은 계획 문서 체크박스를 [x]로 갱신해 해당 커밋에 포함.
- 막히면 추측하지 말고 중단 후 질문.
- 범위 완료 시: M7 게이트(클린 재빌드 완주·키 무효 폴백 재생·README 단독 기동)를 검증하고 보고한 뒤 멈출 것. PR 생성은 내가 지시할 때만.

이 세션 특이사항:
- 실 ANTHROPIC_API_KEY 필요(리허설 record + 인젝션 시연). 인젝션 페이로드 시연 결과(등급 불변)는 verification/injection_payloads.md에 기록.
```

## S7 — M8 LLM 공급자 Gemini 전환 (Task 29–33)

```
executing-plans 스킬을 사용해 docs/plans/mvp-implementation.md 계획을 실행해줘.

이번 세션 범위: Task 29~33 (M8 LLM 공급자 Gemini 전환)만. 범위 밖 태스크는 절대 건드리지 말 것 — Task 1~28은 완료된 이력이므로 본문·Step 기록·DoD를 소급 수정하지 않는다(계획 문서의 '저장소 파일 구조' 항 표기도 마찬가지).
브랜치: PR #27(TDD v0.6 — Gemini 전면 전환 반영)이 머지된 최신 베이스에서 feat/m8-gemini 분기. main 직접 작업 금지.

사양 authority: docs/tdd.md v0.6 §4.2·§4.6·§6·§8·§11 항목 9 + 협의체_기록/LLM_공급자_Gemini_전면전환_TDD반영_검토요청.md. 계획 M8 절의 서술과 어긋나면 TDD가 우선하고, 둘 다로 판단이 서지 않으면 멈추고 물을 것.

규칙:
- 계획의 Global Constraints(G1~G16)·각 태스크 선행 조건·DoD를 그대로 따를 것. 특히 G2(시크릿 마스킹·SEC-* LLM 미경유)·G3(등급 결정론 — LLM 경유 발견은 항상 review_needed)·G9(llm_model_id는 응답 값 기록)는 공급자가 바뀌어도 그대로다. 이 3건을 건드려야 할 것 같으면 그게 잘못 가고 있다는 신호이니 멈추고 물을 것.
- 전환은 transport 계층에 국한한다. docker-compose.yml·api/app/models.py·web/·파이프라인 판정 로직은 변경 금지. AGENTS.md의 「Commit Attribution」 절(Co-Authored-By: Claude …)은 저장소 코딩 에이전트 표기이므로 절대 바꾸지 말 것.
- Task 29~31은 한 덩어리다 — 중간 커밋에서 테스트가 red일 수 있고 green 판정은 Task 31 Step 3에서 한 번에 한다. 회귀는 반드시 docker compose run 경로로 돌릴 것(호스트에 semgrep·gitleaks 바이너리가 없다). 직전 기준선 146건보다 줄면 멈추고 보고.
- 파일 편집은 Write/Edit 도구로. Bash의 sed·heredoc 편집 금지.
- 완료 스텝은 계획 문서 체크박스를 [x]로 갱신해 해당 커밋에 포함.
- 막히면 추측하지 말고 중단 후 질문.
- 범위 완료 시: M8 게이트(계획 '마일스톤 순서' 표 M8행 — 전환 게이트 4건 포함)를 실제 명령으로 검증하고 테스트 출력 요약과 함께 보고한 뒤 멈출 것. PR 생성은 내가 지시할 때만.

이 세션 특이사항:
- 실 GEMINI_API_KEY 필요(Task 32 게이트 4건). .env에 없으면 Task 29~31·33까지만 하고 Task 32는 보류 표시 후 나에게 키를 요청할 것. ANTHROPIC_API_KEY는 폐기 — .env·.env.example에서 지운다.
- 키 값은 코드·문서·로그·커밋 어디에도 남기지 말 것.
- 의존성 교체이므로 docker compose build api(이미지 재빌드) 없이는 SDK가 컨테이너 안에 없다.
- 파라미터 매핑이 1:1이 아니다 — 특히 타임아웃 단위(초 → 밀리초)와 usage 필드명(usage_metadata.prompt_token_count·candidates_token_count), 응답 모델 ID(model_version). 계획 Task 30의 매핑 표를 그대로 따를 것.
- 안전 필터는 전 카테고리 최소 차단으로 설정한다 — 시크릿·PII·인젝션 스니펫이 이 제품의 정상 입력이기 때문이다(TDD §6).
- Task 32 게이트 4건 중 하나라도 실패하면 스스로 우회하지 말고 정지 후 보고. 예비 공급자 경로가 없어 폴백은 "LLM 단계 데모 제외"뿐이고, 그건 TDD §7 MVP 경계선 개정(기획 승인)이 선행되어야 하는 결정이다.
- 실측은 docs/measurements.md에 신규 엔트리로 기록(기존 엔트리 소급 수정 금지) + 계획 '실측 기록' 섹션에 요약 append.
- 완료 보고에 "기획 회신 대기 2건(모델 가정 승인 · 게이트 미충족 시 처리 사전 승인 — TDD §11 항목 9 ①③)" 리마인드를 포함할 것.
```

---

## 병렬 변형 프롬프트 (S1 완료 후 레인 B·C, 병합 후 S3b)

### S3a — 레인 B: M4 전반 (Task 12–14, S2와 병렬)

```
executing-plans 스킬을 사용해 docs/plans/mvp-implementation.md 계획을 실행해줘.

이번 세션 범위: Task 12~14 (gitleaks·한국형 PII·마스킹 P0-2)만. Task 15~16은 이 세션에서 하지 말 것(별도 세션).
브랜치: M1 병합된 베이스에서 feat/m4-core 분기 — S2(feat/m2-m3-sbom-vuln)와 병렬 진행 중이므로 api/app/engine/pipeline.py 연결부와 api/app/config.py 외에는 S2 영역(deps_*·sbom·osv·kisa·semgrep_runner)을 수정하지 말 것.

규칙:
- 계획의 Global Constraints(G1~G16)·각 태스크 선행 조건·DoD를 그대로 따를 것. 특히 G2: 시크릿 원문은 DB·로그 어디에도 남기지 말 것.
- 태스크별 스텝 순서(테스트 작성→실패 확인→구현→green→커밋) 엄수. 완료 스텝은 계획 문서 체크박스를 [x]로 갱신해 해당 커밋에 포함.
- 막히면 추측하지 말고 중단 후 질문.
- 범위 완료 시: Task 12~14 DoD를 검증하고 보고한 뒤 멈출 것. PR 생성은 내가 지시할 때만.

이 세션 특이사항:
- API 키 불필요(Task 12~14는 LLM 미사용).
- 완료 보고에 "S2와 병합 시 pipeline.py·config.py 충돌 확인 필요"를 명시할 것.
```

### S3c — 레인 C: FE 골격 (Task 23, S2·S3a와 병렬)

```
executing-plans 스킬을 사용해 docs/plans/mvp-implementation.md 계획을 실행해줘.

이번 세션 범위: Task 23 (FE API 클라이언트 + 입력·진행 화면)만. 다른 태스크는 절대 건드리지 말 것.
브랜치: M1 병합된 베이스에서 feat/fe-skeleton 분기 — web/ 디렉토리만 수정할 것(api/ 금지).

규칙:
- 계획의 Global Constraints(G1~G16)·Task 23 선행 조건·DoD를 그대로 따를 것.
- 계획의 수동 검증 체크리스트를 브라우저로 실제 수행하고 항목별 결과를 보고. tsc --noEmit·npm run build 클린 필수.
- 완료 스텝은 계획 문서 체크박스를 [x]로 갱신해 해당 커밋에 포함.
- 막히면 추측하지 말고 중단 후 질문.
- 범위 완료 시: Task 23 DoD를 검증하고 보고한 뒤 멈출 것. PR 생성은 내가 지시할 때만.

이 세션 특이사항:
- 백엔드 리포트 API가 아직 없으므로 수동 검증은 스캔 시작·진행 단계 표시까지만(리포트 화면 검증은 S5'에서).
- 완료 시 이후 S5'는 Task 22·24·25만 남는다는 것을 보고에 명시.
```

### S3b — M4 후반 (Task 15–16, S2·S3a 병합 후)

```
executing-plans 스킬을 사용해 docs/plans/mvp-implementation.md 계획을 실행해줘.

이번 세션 범위: Task 15~16 (개인정보·보조 룰 + LLM judge)만. 범위 밖 태스크는 절대 건드리지 말 것.
브랜치: S2·S3a가 모두 병합된 최신 베이스에서 feat/m4-llm 분기. 시작 전에 두 브랜치 병합 완료 여부를 확인하고, 안 되어 있으면 멈추고 알릴 것(Task 15는 Task 11 semgrep 러너, Task 16은 Task 14 마스킹에 의존).

규칙:
- 계획의 Global Constraints(G1~G16)·각 태스크 선행 조건·DoD를 그대로 따를 것. 특히 G2(SEC-* LLM 미경유)·G3(LLM 경유 발견은 항상 review_needed).
- 태스크별 스텝 순서(테스트 작성→실패 확인→구현→green→커밋) 엄수. 완료 스텝은 계획 문서 체크박스를 [x]로 갱신해 해당 커밋에 포함.
- 막히면 추측하지 말고 중단 후 질문.
- 범위 완료 시: M4 게이트 전체를 검증하고 보고한 뒤 멈출 것. PR 생성은 내가 지시할 때만.

이 세션 특이사항:
- Task 16 Step 4(실호출 실측)만 실키 필요 — 없으면 그 스텝만 보류 표시 후 나에게 요청.
- 실측 결과는 docs/measurements.md와 계획 '실측 기록' 섹션에 기록(§11 항목 1·3).
- 완료 보고에 "기획 벤치마크 목록(§11 항목 2) 확정 필요 — M7 착수 전 마감" 리마인드 포함.
```
