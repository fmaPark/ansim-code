# 변경 이력

이 번들의 **문서 단위** 변경 이력이다. 문서별 상세 개정 이력(어떤 조항·어떤 결정이 바뀌었는지)은 각 문서 말미의 개정 이력 표가 정본이며, 이 파일은 그 롤업이다.

## 2026-08-30

* **Update**: `plans/mvp-implementation.md` — Task 26·27을 벤치마크 명세 v0.3(PR #12 머지본) 기준으로 재작성. Task 26 Interfaces에 **룰별 오라클 키 표**(SCA-01~09=패키지 / SCA-10~12=declared_in / P8·P9·P1=repo-wide)와 매칭 의미론(대표 키잉·다발 허용·부가 발견 3단 표)을 도입해 `(rule_id, file)` 일괄 매칭 서술을 폐기, 스텝을 4→7개로 분해(불변식 자동 검사 + CI 신설, `measure_detection.py` 사양화, Flask severity·플레이스홀더·등급 태그 3종 확정, stretch 세트 선택 스텝). Task 27에 **P8·P9·P10 FPR 측정 책임**과 인젝션 페이로드 변형 2~3종을 추가. v0.3 재리뷰분 반영 — B6(SCA-09=django 대표·SCA-08 package는 스캐폴딩 기입)·M1(P4 불변식을 PII·외부전송 동시 등장 조건으로 완화)·M2(명세 §5.1이 매칭 사양의 정본). §11 항목 2 상태를 '미확정'→'확정(게이트 통과)'으로 갱신하고 Task 26 Step 1을 완료 처리. 저장소 구조에 `verification/check_invariants.py` 등재.

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
