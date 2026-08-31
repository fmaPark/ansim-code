---
okf_version: "0.2"
---

# 안심코드(AnsimCode) 지식 번들

생성형 AI 바이브코딩으로 만들어진 앱의 소스코드를 **TTA 표준 4종의 조항 단위로 자동 진단**하는 웹 서비스의 설계·결정·실행 문서 묶음이다. 2026 ICT 표준 챌린지 공모전 데모를 목표로 한다.

이 디렉토리는 [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) 번들이다. 각 문서는 YAML frontmatter에 `type`·`sources`·`generated`·`verified`·`status`·`stale_after`를 싣고, 본문 상단의 사람이 읽는 헤더 표를 함께 유지한다.

## 설계 · 결정

* [TDD — 안심코드](tdd.md) - TTA 표준 4종 조항을 진단 룰 31종으로 구현하는 웹 서비스의 설계 명세. 아키텍처·룰 카탈로그·등급 결정론·P0 3건·리스크·미확정 9건.
* [ADR-001 플랫폼 선정](platform-decision.md) - 웹 vs 데스크톱 vs 하이브리드 결정과 근거. 웹 + 보안 강화로 확정, 등급 공개는 git 전용 소유 증명으로 한정.
* [SEED Design 기반 프론트엔드 재설계 명세](superpowers/specs/2026-08-31-seed-design-redesign.md) - 화면 4종(홈·진행·리포트·공개 등급)의 시각 시스템·레이아웃·접근성 요구사항. 계획 Task 23의 "UI 라이브러리 미도입" 가정을 뒤집고 SEED Design을 도입한 근거를 담는다.

## 실행

* [MVP Implementation Plan](plans/mvp-implementation.md) - 7개 마일스톤 28개 태스크의 실행 계획. 각 태스크에 TDD 참조와 DoD를 병기했다.
* [이슈 #30·#33·#34 심각도 평가와 해결 계획](plans/2026-08-30-issues-30-33-34-remediation.md) - M7이 기록만 남긴 후속 이슈 3건의 심각도를 등급 기여·검출 방향으로 매기고 코드 수정 1건·문서화 2건으로 방침을 확정했다.
* [SEED Design 재설계 구현 계획](superpowers/plans/2026-08-31-seed-design-redesign.md) - 위 명세를 React 19.2·Vite 8 앱에 적용하는 테스트 우선 실행 계획. Task 5개와 자동·Playwright 검증 스텝을 담는다.
* [데모 스크립트](demo-script.md) - 촬영·시연 7장면의 순서와 장면별 사전 상태·근거 조항·내레이션 포인트. 시간이 모자랄 때의 포기 순서 포함.
* [실측 기록](measurements.md) - 벤치마크 TPR·FPR, PyGoat·자기진단 결과, 확인된 룰 갭과 오탐 원인.

## 프로세스

* [AI 활용 정리](ai-usage.md) - 이 프로젝트를 만드는 데 AI를 어떻게 썼는지. 제출문서 작성용 요약 + 전체 워크플로우(설계→계획→프롬프트→실행 문서 체인, 가드레일, 모델 규칙) + 대표 세션 7건 + AI 결과 검증 방법.

## 표준 참고자료

* [참고자료 색인](references/index.md) - TTA 표준 4종(0259 보안취약점 관리·0309 SBOM 속성·0322 SBOM 거버넌스·0414 AI 개인정보보호)과 정부 발간 가이드의 원문 마크다운 변환본.
* [소프트웨어 개발보안 가이드(2021)](references/sw-dev-security-guide-2021/index.md) - 행정안전부·한국인터넷진흥원. 설계단계 보안설계 기준 20개 항목과 구현단계 보안약점 제거 기준 49개 항목의 원문 기준. 376쪽 원문의 장 단위 마크다운 변환본.
* [조항 색인](references/clause-index.md) - 설계 문서가 인용하는 조항 44건을 원문 위치로 연결한다.

## 이력

* [log.md](log.md) - 이 번들의 문서 단위 변경 이력. 문서별 상세 개정 이력은 각 문서 말미의 개정 이력 표에 있다.

## 번들 밖 관련 자료

* `../협의체_기록/` - 기획–개발 검토 왕복 기록. TDD·ADR의 `sources`가 상대 경로로 참조한다.
