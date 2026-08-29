---
okf_version: "0.2"
---

# 안심코드(AnsimCode) 지식 번들

생성형 AI 바이브코딩으로 만들어진 앱의 소스코드를 **TTA 표준 4종의 조항 단위로 자동 진단**하는 웹 서비스의 설계·결정·실행 문서 묶음이다. 2026 ICT 표준 챌린지 공모전 데모를 목표로 한다.

이 디렉토리는 [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) 번들이다. 각 문서는 YAML frontmatter에 `type`·`sources`·`generated`·`verified`·`status`·`stale_after`를 싣고, 본문 상단의 사람이 읽는 헤더 표를 함께 유지한다.

## 설계 · 결정

* [TDD — 안심코드](tdd.md) - TTA 표준 4종 조항을 진단 룰 31종으로 구현하는 웹 서비스의 설계 명세. 아키텍처·룰 카탈로그·등급 결정론·P0 3건·리스크·미확정 8건.
* [ADR-001 플랫폼 선정](platform-decision.md) - 웹 vs 데스크톱 vs 하이브리드 결정과 근거. 웹 + 보안 강화로 확정, 등급 공개는 git 전용 소유 증명으로 한정.

## 실행

* [MVP Implementation Plan](plans/mvp-implementation.md) - 7개 마일스톤 28개 태스크의 실행 계획. 각 태스크에 TDD 참조와 DoD를 병기했다.

## 표준 참고자료

* [TTA 표준 4종](references/index.md) - 0259(보안취약점 관리)·0309(SBOM 속성)·0322(SBOM 거버넌스)·0414(AI 개인정보보호) 원문 마크다운 변환본.
* [조항 색인](references/clause-index.md) - 설계 문서가 인용하는 조항 44건을 원문 위치로 연결한다.

## 이력

* [log.md](log.md) - 이 번들의 문서 단위 변경 이력. 문서별 상세 개정 이력은 각 문서 말미의 개정 이력 표에 있다.

## 번들 밖 관련 자료

* `../협의체_기록/` - 기획–개발 검토 왕복 기록. TDD·ADR의 `sources`가 상대 경로로 참조한다.
