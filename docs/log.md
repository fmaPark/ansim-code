# 변경 이력

이 번들의 **문서 단위** 변경 이력이다. 문서별 상세 개정 이력(어떤 조항·어떤 결정이 바뀌었는지)은 각 문서 말미의 개정 이력 표가 정본이며, 이 파일은 그 롤업이다.

## 2026-08-31

* **Creation**: `ai-usage.md` — 개발 프로세스의 AI 활용 정리. **제출문서 작성자가 참고하는 문서**이므로 맨 앞에 요약(숫자 표 + 특징 5가지)을 두고 세션 전수 나열 대신 대표 7건만 실었다. 근거는 `logs/agent/` 세션 백업 23건(2026-08-24~08-31)과 PR 27건·이슈 14건·커밋 123건. ①전체 워크플로우(설계→계획→프롬프트→실행 4단 문서 체인, 프롬프트 전담 세션 「프롬프트 발사대」, 세션=마일스톤=브랜치=PR 분할, G1~G16을 프롬프트가 아닌 문서에 두는 가드레일, 계획=Fable 5 / 구현=Opus 5 고정 규칙과 커밋 귀속 표기, 세션 기록 자동화와 저장소 규약 정비, 이슈 트래커=다음 세션 입력) ②대표 세션 7건 + 구현 세션 공통 틀 + 사람 개입 지점 ③AI 결과 검증(정답지 기획 선확정 게이트, 자기진단 오탐 3종, 제품 LLM 통제와 인젝션 4종 실증, 기록으로 남은 실패 5건). 번들 밖 로그를 근거로 삼으므로 `sources`에 그 사실을 명시한다. §4는 기획 확인 필요 2건(claude.ai 08-24~08-28 협의 구간, 기획 쪽 PR 리뷰 작성 방식)과 개발 쪽 결손(PR #37·#41 세션 미백업). `index.md`에 「프로세스」 절 신설.

## 2026-08-30

* **Update**: `measurements.md`(「후속 이슈 처리 2회차」 신설) · `demo-script.md`(장면 ⑥) · 루트 `README.md`(「검증」) — #34 잔여분 수정 결과(P9가 자기진단에서 정탐 발화, 수정 전후 P9를 끄는 파일 3→0건)와 #33·#30의 방침 확정을 기록. #33은 룰 31종 중 **실효 29종**임을 README에 명시(SCA-05·SCA-07은 레지스트리 원격 조회가 없어 입력이 비어 있다) — `rules/catalog.yaml`은 건드리지 않아 `rule_catalog_version`은 유지된다. #30은 룰 소스 자기 발화를 기록으로 닫고 semgrep 이관을 V2로 넘긴다. 데모 장면 ⑥에 P5(자기 발화·등급 무영향)와 P9(정탐·등급 기여)를 구분해 설명하는 대본을 넣었다.
* **Creation**: `plans/2026-08-30-issues-30-33-34-remediation.md` — M7이 기록만 남긴 후속 이슈 3건의 심각도 평가와 처리 방침. 등급 기여(`confirmed`만 등급을 움직인다)와 오류 방향(미검출이 오탐보다 나쁘다) 두 기준으로 #34 High·#33 Medium·#30 Low로 매기고, #34만 코드 수정하고 #33·#30은 문서화로 닫는다. #34 라우트 검사의 잔여 한계와 #30을 같은 뿌리(정규식은 패턴을 정의한 소스와 사용한 소스를 구분하지 못한다)로 묶어 semgrep 이관을 V2 후보로 기록했다.
* **Update**: `tdd.md` v0.6 — **LLM 공급자 전면 전환**(Anthropic Claude → Google Gemini). 기획 비용 절감 요청에 따른 같은 날 확정으로, Anthropic 경로는 코드에 남기지 않고(복구는 git 이력) `ANTHROPIC_API_KEY`를 폐기한다. §3 In Scope·§4.1 아키텍처·§4.2 기술 스택(모델 가정·`model_version` 기록·thinking 비활성·안전 필터)·§4.6 외부 의존성·§4.7 시퀀스·§4.8 배포·§6 리스크(장애 행 갱신 + 안전 필터 차단 행 신설)·§8 API 키 관리·§11 항목 9 갱신. **등급 결정론(§4.5)·마스킹(P0)·G1~G16은 무변경** — 전환은 transport 계층에 국한된다.
* **Update**: `plans/mvp-implementation.md` — **M8(LLM 공급자 Gemini 전환) 신설**, Task 29~33 추가(의존성·설정 교체 / `client.py` transport 재작성 / judge·convert·테스트 갱신 / 전환 게이트 실측 4건 / README·AGENTS 동기). Tech Stack 줄·마일스톤 표·§11 항목 9 행 갱신. Task 1~28의 본문·Step·DoD는 이력 기록이라 소급 수정하지 않았다.
* **Update**: `plans/execution-prompts.md` — S7(M8 · Task 29~33) 실행 프롬프트 신설, 세션 표에 S7 행 추가.
* **Update**: `measurements.md` — M8 전환 게이트 4건 실측 엔트리 신규. 안전 필터 차단 0/5·`model_version` 기록 확인·캐시 폴백 재생 완주는 통과, judge 12 병렬은 무료 티어 쿼터(5 RPM·**20 RPD**)로 실패. TDD §4.2 모델 가정 2종이 실호출 404라 judge=`gemini-3.5-flash`·변환=`gemini-3.1-flash-lite`로 정정(기획 사후 승인).
* **Update**: `plans/mvp-implementation.md` — Task 26·27을 벤치마크 명세 v0.3(PR #12 머지본) 기준으로 재작성. Task 26 Interfaces에 **룰별 오라클 키 표**(SCA-01~09=패키지 / SCA-10~12=declared_in / P8·P9·P1=repo-wide)와 매칭 의미론(대표 키잉·다발 허용·부가 발견 3단 표)을 도입해 `(rule_id, file)` 일괄 매칭 서술을 폐기, 스텝을 4→7개로 분해(불변식 자동 검사 + CI 신설, `measure_detection.py` 사양화, Flask severity·플레이스홀더·등급 태그 3종 확정, stretch 세트 선택 스텝). Task 27에 **P8·P9·P10 FPR 측정 책임**과 인젝션 페이로드 변형 2~3종을 추가. v0.3 재리뷰분 반영 — B6(SCA-09=django 대표·SCA-08 package는 스캐폴딩 기입)·M1(P4 불변식을 PII·외부전송 동시 등장 조건으로 완화)·M2(명세 §5.1이 매칭 사양의 정본). §11 항목 2 상태를 '미확정'→'확정(게이트 통과)'으로 갱신하고 Task 26 Step 1을 완료 처리. 저장소 구조에 `verification/check_invariants.py` 등재.
* **Update**: `tdd.md` v0.5(§4.1 아키텍처 다이어그램·§4.2 기술 스택 표) / `plans/mvp-implementation.md`(Tech Stack) — 프론트엔드 표기를 React 18 → **React 19.2**로 정정. 실제 구현이 `web/package-lock.json` 기준 react·react-dom 19.2.8이라 설계 문서 표기와 어긋나 있었다. 설계 판단 변경이 아닌 표기 정정이므로 `plans/mvp-implementation.md`·`platform-decision.md`의 "TDD v0.4" 참조(그 판단 집합을 근거로 삼았다는 기록)는 그대로 둔다.
* **Creation**: 루트 `AGENTS.md` — 에이전트용 저장소 지침(스택·파일 단위 명령·규약). `CLAUDE.md`는 `@AGENTS.md` import 한 줄만 두어 내용 분기를 차단한다(심링크는 Windows 클론에서 평문 파일로 깨지므로 쓰지 않는다). 이 번들 밖 파일이라 OKF frontmatter 대상이 아니다.

## 2026-08-29

* **Creation**: `references/sw-dev-security-guide-2021/` — 행정안전부·한국인터넷진흥원 「소프트웨어 개발보안 가이드」(2021.11., 376쪽) 원문 전체의 장 단위 마크다운 변환본 5건 + 색인. 설계단계 보안설계 기준 20개(SR1-1 ~ SR4-1)와 구현단계 보안약점 제거 기준 49개의 원문 기준이다.
* **Update**: `references/index.md` — 「TTA 정보통신단체표준」과 「정부 발간 가이드」로 수록 문서를 두 갈래로 나누고 개발보안 가이드를 등재.
* **Update**: OKF v0.2 번들 구조 도입 — 8개 문서에 frontmatter(`type`·`sources`·`generated`·`status`) 추가, 루트 `index.md` 신설, `references/README.md` → `references/index.md` 개명.
* **Creation**: `references/clause-index.md` — 설계 문서가 인용하는 TTA 표준 조항 44건의 원문 위치 색인.
* **Creation**: `log.md` — 이 파일.
* **Update**: `plans/mvp-implementation.md` — TDD §11 미확정 8항목의 처리 방침 확정, 저장소 파일 구조에 `tools/` 추가.
* **Creation**: `plans/mvp-implementation.md` — 7 마일스톤 28 태스크 실행 계획(TDD v0.4·ADR-001 v1.3 기반). 일정을 일자 분기에서 순차 마일스톤 + 선행 조건으로 변경(7일은 상한).
* **Creation**: `references/` — TTA 표준 4종 마크다운 변환본.

## 2026-08-28

* **Update**: `tdd.md` v0.4 / `platform-decision.md` v1.3 — 최종 확정 명세 반영. P0 3건(파기 finally·시크릿 마스킹·등급 결정론), 조항 오귀속 정정(주석 검사 §9.3→§9.5), 개인정보 룰 10종 확정, 등급 결정론·상향 조건, 공개는 git 전용 + `.ansimcode` 소유 증명(zip 공개 제외).

## 2026-08-26

* **Update**: `platform-decision.md` v1.3 — zip 등급 공개를 v1.2에서 번복해 제외. "지문은 동일성 증명이지 공개 권한 증명이 아니다"라는 기획 검토와 "zip 공개 = 소유 증명 우회로"라는 개발 검토를 반영.

## 2026-08-24

* **Update**: `platform-decision.md` v1.2 — zip 콘텐츠 지문(정규화 파일 트리 SHA-256) 채택, 스캔별 `rule_catalog_version`·`llm_model_id` 기록 추가(기획 accept).
* **Update**: `platform-decision.md` v1.1 — 기획 검토 4건 반영. §7.3.5 적용 논리 보강, 입력 경로별 리스크 프로파일 구분, 등급 재현성(커밋 해시), 데모 시연 대비.
* **Creation**: `platform-decision.md` v1.0 — ADR-001 플랫폼 선정. 웹 + 보안 강화로 확정.
* **Creation**: `tdd.md` v0.1 — 최초 작성.
