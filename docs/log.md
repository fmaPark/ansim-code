# 변경 이력

이 번들의 **문서 단위** 변경 이력이다. 문서별 상세 개정 이력(어떤 조항·어떤 결정이 바뀌었는지)은 각 문서 말미의 개정 이력 표가 정본이며, 이 파일은 그 롤업이다.

## 2026-08-30

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
