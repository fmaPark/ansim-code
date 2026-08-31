---
type: Playbook
title: SEED Design 기반 안심코드 프론트엔드 고도화 구현 계획
description: 승인된 SEED Design 재설계 명세를 React 19.2·Vite 8 앱에 적용하는 테스트 우선 실행 계획.
status: active
tags: [ansimcode, plan, frontend, seed-design]
generated: { by: "OpenAI Codex", at: "2026-08-31T00:00:00+09:00" }
stale_after: "2026-09-30T00:00:00+09:00"
sources:
  - { id: spec, resource: ../specs/2026-08-31-seed-design-redesign.md, title: "SEED Design 기반 안심코드 프론트엔드 재설계", author: "OpenAI Codex", last_modified: "2026-08-31" }
---

# SEED Design 기반 안심코드 프론트엔드 고도화 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 기능과 문구를 유지하면서 홈·진행·리포트·공개 등급을 SEED Design 기반의 접근 가능하고 반응형인 보안 진단 UI로 고도화한다.

**Architecture:** SEED의 사전 빌드 CSS와 React 컴포넌트를 Vite 플러그인으로 통합한다. 일반 앱 레이아웃과 고밀도 표는 프로젝트 CSS로 유지하고, 상호작용 컴포넌트만 작은 로컬 래퍼를 통해 SEED API에 연결한다.

**Tech Stack:** React 19.2, TypeScript 6, Vite 8, React Router 7, SEED Design 2.x, Vitest, Testing Library, 일반 CSS.

**Spec:** [docs/superpowers/specs/2026-08-31-seed-design-redesign.md](../specs/2026-08-31-seed-design-redesign.md)

## Global Constraints

- Tailwind CSS를 설치하지 않는다.
- `web/package-lock.json`을 의존성 버전의 정본으로 유지한다.
- API, 라우트 경로, 진단 단계명, 사용자 노출 문구를 임의로 변경하지 않는다.
- `@seed-design/css/vars/component/*` 내부 변수에 직접 의존하지 않는다.
- 당근 로고와 브랜드 자산을 사용하지 않는다.
- 라이트 모드만 구현한다.
- 테스트는 상호작용 변경 전에 실패를 확인하고 구현 후 통과를 확인한다.

---

### Task 1: SEED와 테스트 기반 통합

**Files:**
- Modify: `web/package.json`
- Modify: `web/package-lock.json`
- Modify: `web/vite.config.ts`
- Modify: `web/src/main.tsx`
- Create: `web/src/test/setup.ts`
- Create: `web/src/test/render.tsx`
- Create: `web/src/components/ui/ActionButton.tsx`
- Test: `web/src/components/ui/ActionButton.test.tsx`

**Interfaces:**
- Produces: `ActionButton(props)` compatible with `button` attributes and `loading?: boolean`.
- Produces: `renderWithRouter(ui, initialEntries?)` for page tests.

- [ ] **Step 1: Install the exact dependency set with npm**

Run from `web`:

```powershell
npm install @seed-design/react @seed-design/css @seed-design/vite-plugin
npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

- [ ] **Step 2: Add the test script and Vitest environment**

Add `"test": "vitest run"` to scripts and configure `test.environment = "jsdom"`, `setupFiles = ["./src/test/setup.ts"]` in `vite.config.ts`. Add `seedDesignPlugin({ colorMode: "light-only" })` after the React plugin.

- [ ] **Step 3: Write a failing ActionButton loading-state test**

```tsx
it('disables the button and exposes busy state while loading', () => {
  render(<ActionButton loading>진단 시작</ActionButton>)
  expect(screen.getByRole('button', { name: '진단 시작' })).toBeDisabled()
  expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true')
})
```

- [ ] **Step 4: Run the focused test and verify RED**

Run: `npm test -- src/components/ui/ActionButton.test.tsx`

Expected: FAIL because `ActionButton` does not exist or does not expose the loading semantics.

- [ ] **Step 5: Implement the minimal SEED ActionButton wrapper**

Wrap `@seed-design/react` ActionButton, map `loading` to `disabled` and `aria-busy`, preserve ref and native click behavior, and import SEED base CSS once from `main.tsx`.

- [ ] **Step 6: Run the focused test and build**

Run: `npm test -- src/components/ui/ActionButton.test.tsx`

Expected: PASS.

Run: `npm run build`

Expected: exit 0 with SEED CSS resolved.

### Task 2: 공통 셸과 홈 화면

**Files:**
- Modify: `web/src/App.tsx`
- Modify: `web/src/pages/Home.tsx`
- Create: `web/src/styles/tokens.css`
- Create: `web/src/styles/base.css`
- Create: `web/src/styles/home.css`
- Modify: `web/src/styles.css`
- Test: `web/src/pages/Home.test.tsx`

**Interfaces:**
- Consumes: `ActionButton`, `renderWithRouter`.
- Produces: `.app-shell`, `.site-header`, `.page`, `.scan-panel`, `.dropzone` layout contracts.

- [ ] **Step 1: Write failing Home interaction tests**

Cover: non-HTTPS URL displays `공개 https git URL만 지원합니다`; busy state disables the primary action; non-zip upload shows the existing file-type error; the visible H1 and CTA copy remain unchanged.

- [ ] **Step 2: Run Home tests and verify RED**

Run: `npm test -- src/pages/Home.test.tsx`

Expected: FAIL on new SEED control roles or wrapper semantics before the page migration.

- [ ] **Step 3: Implement the common shell and Home composition**

Replace only presentation markup. Keep `begin`, `submitGit`, `acceptZip`, API calls and navigation unchanged. Use the approved desktop/mobile container model and SEED controls; preserve native file input and drag events.

- [ ] **Step 4: Implement tokens and responsive Home CSS**

Define true-white background, cool gray surfaces, navy foreground, teal-blue action, semantic grade colors, type scale, spacing, radii, borders and focus ring. At `max-width: 640px`, stack the URL field and action, reduce page gutters, and keep the dropzone within viewport.

- [ ] **Step 5: Run Home tests, lint and build**

Run: `npm test -- src/pages/Home.test.tsx`

Run: `npx oxlint src/App.tsx src/pages/Home.tsx src/components/ui/ActionButton.tsx`

Run: `npm run build`

Expected: all exit 0.

### Task 3: 진단 진행과 공개 등급

**Files:**
- Modify: `web/src/pages/ScanProgress.tsx`
- Modify: `web/src/pages/PublicGrade.tsx`
- Create: `web/src/styles/progress.css`
- Create: `web/src/styles/public-grade.css`
- Test: `web/src/pages/ScanProgress.test.tsx`
- Test: `web/src/pages/PublicGrade.test.tsx`

**Interfaces:**
- Consumes: global shell and token contracts.
- Produces: accessible five-stage tracker and public provenance disclosure.

- [ ] **Step 1: Write failing ScanProgress tests**

Verify the five exact stage labels render, the active stage exposes `aria-current="step"`, and a failed scan exposes the existing error and home link.

- [ ] **Step 2: Run ScanProgress tests and verify RED**

Run: `npm test -- src/pages/ScanProgress.test.tsx`

Expected: FAIL because the current step does not expose `aria-current` and the new progress structure is absent.

- [ ] **Step 3: Implement the progress screen**

Keep polling and navigation unchanged. Add an accessible circular progress visual, explicit current status, semantic ordered stage list, and reduced-motion handling.

- [ ] **Step 4: Write failing PublicGrade tests**

Verify owner disclosure, grade, formatted scan time, easy descriptions, provenance `<details>`, and final disclaimer are present using API-shaped fixture data.

- [ ] **Step 5: Run PublicGrade tests and verify RED**

Run: `npm test -- src/pages/PublicGrade.test.tsx`

Expected: FAIL on the new structured region labels before migration.

- [ ] **Step 6: Implement the public grade screen**

Preserve the data request and all existing fields. Recompose the page without certificate imagery, add semantic section headings and style the native details/table disclosure.

- [ ] **Step 7: Run focused tests, lint and build**

Run: `npm test -- src/pages/ScanProgress.test.tsx src/pages/PublicGrade.test.tsx`

Run: `npx oxlint src/pages/ScanProgress.tsx src/pages/PublicGrade.tsx`

Run: `npm run build`

Expected: all exit 0.

### Task 4: 리포트·발견 사항·공개 Dialog

**Files:**
- Modify: `web/src/pages/Report.tsx`
- Modify: `web/src/components/FindingCard.tsx`
- Modify: `web/src/components/GradePill.tsx`
- Modify: `web/src/components/PublishFlow.tsx`
- Modify: `web/src/components/SixPrinciples.tsx`
- Modify: `web/src/components/DiffPanel.tsx`
- Modify: `web/src/components/UpgradeBlock.tsx`
- Create: `web/src/styles/report.css`
- Test: `web/src/components/FindingCard.test.tsx`
- Test: `web/src/components/PublishFlow.test.tsx`
- Test: `web/src/pages/Report.test.tsx`

**Interfaces:**
- Consumes: SEED controls, shared tokens, existing API types.
- Produces: report summary layout, tab navigation, findings disclosure, focus-managed publish Dialog.

- [ ] **Step 1: Write failing FindingCard disclosure test**

Render a fixture finding, click `수정 프롬프트 보기`, verify the prompt and copy action appear, click the control again, and verify the prompt is hidden. Assert `aria-expanded` changes.

- [ ] **Step 2: Run the FindingCard test and verify RED**

Run: `npm test -- src/components/FindingCard.test.tsx`

Expected: FAIL because the current button does not expose disclosure semantics.

- [ ] **Step 3: Implement findings and grade/status presentation**

Preserve data order and anchors. Add semantic badge variants, accessible disclosure state, structured title/location/evidence sections, and mobile-safe wrapping.

- [ ] **Step 4: Write failing publish Dialog test**

Mock `publish`, click `공개하기`, verify a dialog with `등급 공개 — 저장소 소유 증명` opens, then verify close returns focus to the trigger.

- [ ] **Step 5: Run the publish test and verify RED**

Run: `npm test -- src/components/PublishFlow.test.tsx`

Expected: FAIL before SEED Dialog composition and focus restoration are implemented.

- [ ] **Step 6: Implement PublishFlow with SEED Dialog**

Keep token issuance and confirmation calls unchanged. Use SEED Dialog primitives for accessible title, backdrop, content and close behavior. Preserve the zip-disabled explanation.

- [ ] **Step 7: Write failing report integration tests**

With API fixtures, verify the four tabs render, clicking `SBOM` shows its loading state and requests SBOM, clicking the citizen switch shows the easy summary, and the existing primary action labels remain present.

- [ ] **Step 8: Run report tests and verify RED**

Run: `npm test -- src/pages/Report.test.tsx`

Expected: FAIL on the new switch/tab roles before the page migration.

- [ ] **Step 9: Implement report composition and dense-data CSS**

Create the open summary band, responsive action hierarchy, six-principle status grid, horizontally scrollable tabs, finding list, and semantic table styles. Do not add concept-only filters, project metadata or fake counts.

- [ ] **Step 10: Run focused tests, lint and build**

Run: `npm test -- src/components/PublishFlow.test.tsx src/pages/Report.test.tsx`

Run: `npx oxlint src/pages/Report.tsx src/components/FindingTable.tsx src/components/ReportTableFrame.tsx src/components/GradePill.tsx src/components/PublishFlow.tsx src/components/SixPrinciples.tsx`

Run: `npm run build`

Expected: all exit 0.

### Task 5: 전체 검증과 시각 충실도 조정

**Files:**
- Modify as needed: `web/src/**/*.tsx`, `web/src/styles.css`
- Verify: Playwright 1440×1000·390×844 캡처(저장소 밖 로컬 QA 산출물)

**Interfaces:**
- Consumes: all redesigned routes and accepted concepts.
- Produces: verified desktop/mobile implementation and fidelity ledger.

- [ ] **Step 1: Run the complete automated suite**

Run from `web`:

```powershell
npm run test
npm run lint
npm run build
```

Expected: all exit 0 with no relevant warning or error.

- [ ] **Step 2: Start the Vite app and verify browser health**

Run: `npm run dev -- --host 127.0.0.1`

Use Browser/IAB at the reported URL. Check page identity, nonblank DOM, framework overlays, console errors and the primary Home interaction.

- [ ] **Step 3: Capture and compare desktop views**

At 1440x1000 capture Home and, using reachable fixture/API data, Progress, Report and Public Grade. Compare layout, typography, palette, spacing, container model, controls and copy to the accepted concepts.

- [ ] **Step 4: Capture and compare mobile views**

At 390x844 capture Home and Report. Verify no page-level horizontal overflow, correct action wrapping, tab scrolling, principle layout and table-contained horizontal scrolling.

- [ ] **Step 5: Exercise the core interaction path**

Verify invalid URL error, zip file validation, report tab selection, citizen explanation switch, finding disclosure, copy feedback and publish Dialog open/close. Record any backend-data blocker explicitly.

- [ ] **Step 6: Use view_image for the final side-by-side QA pass**

Inspect the accepted concept and latest implementation screenshot in the same pass. Record at least five concrete comparison points and fix every actionable mismatch before completion.

- [ ] **Step 7: Run final verification again after visual fixes**

Run:

```powershell
npm run test
npm run lint
npm run build
```

Expected: all exit 0 after the final rendered fixes.
