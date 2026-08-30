---
type: Technical Design Doc
title: SEED Design 기반 안심코드 프론트엔드 재설계
description: 기존 진단 기능을 유지하면서 SEED Design 컴포넌트와 시맨틱 토큰으로 홈·진행·리포트·공개 등급 화면을 고도화하는 설계 명세.
status: approved
tags: [ansimcode, frontend, seed-design, react, redesign]
generated: { by: "OpenAI Codex", at: "2026-08-31T00:00:00+09:00" }
stale_after: "2026-09-30T00:00:00+09:00"
sources:
  - { id: tdd, resource: ../../tdd.md, title: "안심코드 TDD", author: "human:개발-풀스택", last_modified: "2026-08-30" }
  - { id: seed, resource: "https://github.com/daangn/seed-design", title: "SEED Design System", author: "daangn" }
  - { id: seed-vite, resource: "https://seed-design.io/react/getting-started/installation/vite", title: "SEED Vite 설치", author: "daangn" }
---

# SEED Design 기반 안심코드 프론트엔드 재설계

## 목표

기존 API·라우팅·진단 규칙·문구·업로드·재진단·공개 기능을 바꾸지 않고, 프론트엔드를 신뢰할 수 있는 보안 진단 도구의 시각 체계로 고도화한다. SEED Design은 컴포넌트 구조·상태·타이포그래피·시맨틱 토큰의 기준으로 사용하고, 안심코드 고유의 리포트 밀도와 브랜드 표현은 일반 CSS로 보완한다.

## 확정 접근

- `@seed-design/react`, `@seed-design/css`, `@seed-design/vite-plugin`을 사용한다.
- Tailwind CSS는 도입하지 않는다.
- SEED의 당근 로고·브랜드 이미지·주황색 브랜드 인상은 사용하지 않는다.
- 라이트 모드만 범위에 포함한다. 다크 모드는 후속 작업이다.
- SEED의 안정적인 시맨틱 토큰과 공개 컴포넌트 API만 사용하고 내부 component 변수에 직접 의존하지 않는다.
- 기존 시맨틱 `<table>`은 유지한다. SBOM·체크리스트를 카드 목록으로 바꾸지 않는다.
- 실제 화면 텍스트와 컨트롤은 모두 React/HTML로 구현한다. 콘셉트 이미지를 제품 UI 자산으로 사용하지 않는다.

## 승인된 콘셉트

| 화면 | 데스크톱 | 모바일 |
| --- | --- | --- |
| 홈 | [home-desktop.png](../assets/seed-redesign/home-desktop.png) | [home-mobile.png](../assets/seed-redesign/home-mobile.png) |
| 진행 | [progress-desktop.png](../assets/seed-redesign/progress-desktop.png) | 데스크톱 구조를 단일 열로 축소 |
| 리포트 | [report-desktop.png](../assets/seed-redesign/report-desktop.png) | [report-mobile.png](../assets/seed-redesign/report-mobile.png) |
| 공개 등급 | [public-grade-desktop.png](../assets/seed-redesign/public-grade-desktop.png) | 데스크톱 구조를 단일 열로 축소 |

콘셉트가 임의로 만든 프로젝트명, 진단 ID, 필터, 검색창, 리포트 목록, 도움말, 사용자 아바타, 권장 조치 문구는 구현하지 않는다. 실제 API가 제공하는 데이터와 기존 UI 문구가 정보의 정본이다.

## 시각 시스템

### 색상

- 배경은 순백색과 차가운 밝은 회색으로 구성한다. 크림·베이지·웜그레이로 변경하지 않는다.
- 본문은 짙은 네이비 계열, 보조 텍스트는 중립 회색을 사용한다.
- 주요 동작은 청록이 섞인 딥 블루를 사용한다.
- `안심`은 positive, `주의`는 warning, `위험`은 critical 의미 체계에 대응한다.
- 등급 외 요소에서 상태색을 장식 목적으로 사용하지 않는다.

### 타이포그래피

- 한국어 환경을 위해 `Pretendard`, `Noto Sans KR`, 시스템 산세리프 순서로 폴백한다.
- 페이지 제목 32~44px, 섹션 제목 18~22px, 본문 14~16px, 컨트롤·표 12~14px 범위를 사용한다.
- 버튼, 탭, 입력, 배지, 표 헤더의 크기와 굵기를 명시하고 브라우저 기본값에 맡기지 않는다.

### 형태와 컨테이너

- 데스크톱 최대 콘텐츠 폭은 1160px이다.
- 반경은 10~16px 범위로 제한한다.
- 기본 구조는 열린 레이아웃과 구분선이며, 모든 영역을 카드로 감싸지 않는다.
- 그림자는 주요 입력 패널과 모달에만 약하게 사용한다.
- 포커스 링, hover, pressed, disabled 상태는 SEED 상태 규칙을 따른다.

## 화면 설계

### 공통 셸

- 상단 헤더에는 `안심코드`와 `소스코드 안전 자가진단 — 인증이 아닌 자가점검 보조`만 표시한다.
- 헤더는 단순한 텍스트 브랜드와 하단 구분선으로 구성한다.
- 데스크톱은 1160px, 홈의 주요 작업 영역은 약 900px로 제한한다.
- 모바일에서는 헤더 보조 문구를 숨기고 모든 주요 동작을 전체 너비로 쌓는다.

### 홈

- 허용된 첫 화면 문구는 기존 `Home.tsx`의 브랜드, H1, 설명, 입력 placeholder, CTA, 업로드 안내, 면책 문구뿐이다.
- git URL 입력을 한 개의 명확한 주 작업으로 배치한다.
- zip 업로드는 두 번째 구역으로 유지하며 드래그 상태를 시각적으로 명확히 한다.
- URL 오류와 업로드 오류는 SEED Callout 계열의 critical 상태로 표시한다.
- 모바일은 입력과 버튼을 수직으로 쌓고 dropzone 높이를 줄인다.

### 진단 진행

- 현재 단계를 Progress Circle 중앙에 표시한다.
- 0259 5단계 용어 `환경분석`, `현황진단`, `위험분석`, `대책수립`, `완료`는 그대로 유지한다.
- 데스크톱 스텝퍼는 수평, 모바일은 압축 수평 또는 세로 목록으로 표현한다.
- 실패 상태는 오류 내용과 홈 복귀 동작을 함께 제공한다.
- `prefers-reduced-motion`에서는 회전·펄스 애니메이션을 제거한다.

### 리포트

- 상단은 등급과 실제 제공 가능한 요약값을 중심으로 구성한다. API에 없는 가상 지표는 만들지 않는다.
- 액션 우선순위는 `공개하기` > `전체 수정 프롬프트 복사` > `재진단`이다.
- 시민용 전환은 SEED Switch로 구현하되 기존 boolean 상태를 유지한다.
- 6대 원칙은 데스크톱 6열, 모바일 2열 상태 그리드로 표시한다.
- 탭은 모바일에서 가로 스크롤하며 선택 상태를 명확히 한다.
- 발견 사항은 심각도, 제목, 조항, 판정 상태, 등급 차단, 위치, 근거, 수정 프롬프트 순서를 유지한다.
- 수정 프롬프트는 disclosure 동작과 복사 액션을 유지한다.
- SBOM·체크리스트·공급망 표는 행 밀도와 가로 스크롤을 유지한다.
- 공개하기 흐름은 SEED Dialog로 교체하여 포커스 트랩, Escape 닫기, backdrop 닫기를 제공한다.

### 공개 등급

- 인증서·공식 인증 마크처럼 보이는 인장, 리본, 정부 상징을 사용하지 않는다.
- 등급, 소유자 직접 공개 고지, 진단 시각, 쉬운 설명을 우선한다.
- 재현성 정보는 접근 가능한 `<details>` disclosure를 유지하되 시각 구조를 정돈한다.
- 기존 disclaimer를 하단에서 반복 노출한다.

## 컴포넌트 대응

| 기존 요소 | SEED/구현 방식 |
| --- | --- |
| `.primary`, `.ghost` | `ActionButton` 래퍼 variants |
| git URL `<input>` | SEED Text Field 조합 또는 styled input |
| 오류 배너 | SEED Callout |
| 시민용 checkbox | SEED Switch |
| 탭 버튼 | SEED Tabs |
| 공개 모달 | SEED Dialog |
| 등급·심각도·상태 | SEED Badge + 안심코드 grade variant |
| 진행 spinner | SEED Progress Circle + 전용 단계 표시 |
| 데이터 표 | 시맨틱 `<table>` + 안심코드 CSS |
| 발견 카드 | 전용 `FindingCard` + SEED 버튼/배지 |

## 접근성·반응형

- 모든 상호작용 요소는 키보드로 접근 가능해야 한다.
- `:focus-visible` 표시를 제거하지 않는다.
- 모달은 열릴 때 포커스를 받고 닫힐 때 트리거로 복귀한다.
- 색상만으로 등급·상태를 전달하지 않고 텍스트를 함께 표시한다.
- 390px 너비에서 가로 페이지 overflow가 없어야 한다. 데이터 표 내부 스크롤은 예외다.
- 1440x1000과 390x844를 주요 검증 뷰포트로 사용한다.

## 테스트와 완료 조건

- URL 제출, zip 검증, 시민용 전환, 탭 전환, 수정 프롬프트 disclosure, 공개 Dialog의 상호작용 테스트를 추가한다.
- `npm run lint`, `npm run test`, `npm run build`가 성공해야 한다.
- 브라우저에서 홈의 첫 화면, 모바일 홈, 진행 화면, 리포트, 모바일 리포트, 공개 등급을 확인한다.
- 콘셉트와 구현 스크린샷을 같은 QA 패스에서 직접 비교한다.
- 기존 문구·API·라우팅·진단 기능에 의도하지 않은 변경이 없어야 한다.
