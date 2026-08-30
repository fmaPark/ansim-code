# PR #12 리뷰 분석 및 보완·고도화 계획

| 항목 | 내용 |
| --- | --- |
| 대상 | [PR #12 — docs/benchmark-spec.md v0.1](https://github.com/fmaPark/ansim-code/pull/12) (벤치마크 취약점 목록 확정본 초안, M7 게이트) |
| 목적 | 리뷰 판정 근거를 기록하고, 명세 v0.2 개정과 후속 구현을 서브에이전트 작업 패키지(WP)로 분해한다 |
| 검증 방법 | 명세가 인용한 코드 전부를 현행 main과 대조했다 (`rules/catalog.yaml` · `repo_checks.py` · `pii.py` · `sca_rules.py` · `analysis.py` · `pipeline.py` · `judge.py` · `gitleaks_runner.py` · `imports_py.py` · KISA CSV · TDD §9 · Task 26·27) |
| 작성 | 2026-08-30 |
| 진행 현황 | **PR #12 승인·머지 완료(2026-08-30)** — 리뷰 3회(B1~B5 → B6·M1·M2 → 승인)를 거쳐 v0.3이 M7 게이트를 통과했다. WP-1·WP-2는 이 과정에서 명세 본문에 흡수되어 완료됐고, 다음 착수 지점은 WP-3·WP-4다 |

## 1. 리뷰 판정 요약

명세의 골격(31종 커버리지, 룰별 오라클 키 차등화, repo-wide 마스킹 회피, 등급의 static 재현성)은 실제 코드와 대체로 일치하며, 순환 검증 회피 원칙도 잘 지켜졌다. 다만 코드와 대조한 결과 **사실 오류 1건(P1·P4 키 필요 주장)**, **오라클 YAML의 매칭 불가·누락 5건**, **불변식 적용 범위 오류 1건**을 확인했다. 이 상태로 승인하면 측정 단계(Task 26)에서 오라클이 그대로 쓰이지 못하고 개발이 목록을 고치게 되어, 명세가 지키려던 "기획 선확정" 원칙이 사후에 훼손된다.

**권고: 조건부 승인.** 아래 블로커 B1~B5를 반영한 v0.2 개정판을 같은 PR에 커밋한 뒤 승인 게이트를 통과시킨다.

### 검증으로 확인된 사항 (명세 주장이 옳음)

- 룰 31종 구성(SCA 12 · SEC 5 · P 10 · AUX 4)은 `rules/catalog.yaml`과 일치한다.
- 인용 라인이 모두 정확하다: RRN 무효 기본값 `review_needed`(`pii.py:15`), P8 로깅 부재 판정(`repo_checks.py:98`), P9 처리방침 부재(`repo_checks.py:104`), 삭제 동사 정규식(`repo_checks.py:64`).
- CVE 5핀은 전부 `data/kisa/krcert_notices.csv`에 존재하여 SCA-03 교차가 성립한다.
- '위험' 트리거가 전부 static이라는 §1.4의 등급 재현성 주장은 `grade` 파이프라인 구조(`pipeline.py:249-250`)와 일치한다.
- AUX-01·AUX-03은 JS 변형 룰이 실재하므로(`rules/semgrep/aux-security.yaml:16,47`) `sqli.js`·`server.js`를 confirmed로 기대해도 된다.
- clean/의 플레이스홀더 안전 패턴은 gitleaks allowlist(`rules/gitleaks/ansim.toml:34-37`)와 정확히 대응한다.

## 2. 발견 사항

### 블로커 — v0.2에서 수정해야 승인 가능

**B1. "P1·P4는 LLM 합성이라 키 필요" 주장은 코드와 다르다 (§1.4 · §4.2 · 리뷰 포인트 4).**
P1·P4 초안은 LLM이 아니라 정적 코드가 합성한다(`analysis.py:108-131`의 `synthesize_llm_drafts` — P1은 P2·P3 evidence의 필드 집계, P4는 PII 필드 + `requests.post|fetch(|axios.` 동시 등장 파일 검사). 키가 없으면 judge 단계만 스킵되고 초안은 `review_needed` 상태로 유지된다(`judge.py:54-58`, `pipeline.py:247`). 따라서 **P1·P4의 TPR도 키 없이 측정 가능**하며, "키 없으면 이 2종은 TPR 측정 보류"라는 트레이드오프는 실재하지 않는다. §1.4·§4.2·§8의 해당 서술을 정정한다.

**B2. §5 YAML의 `SEC-??` 플레이스홀더와 §4.5의 페이로드 서술이 Task 27과 충돌한다.**
Task 27 Step 2(`mvp-implementation.md:1891-1895`)는 인젝션 페이로드 원문을 이미 확정했다: `API_KEY = "AKIAIOSFODNN7REALKEY1"` 하드코딩. 이 값은 gitleaks 기본 룰의 `aws-` 접두 매핑으로 **SEC-04**가 된다(`gitleaks_runner.py:27,42-43`). §4.5의 "평문 카드번호 저장" 서술은 이 원문과 다르고, 카드·계좌 패턴은 `classify_secret`에서 review_needed로 분기되어(`pii.py:47`) "confirmed 정상 flag + 등급 유지" 시연 의도와도 어긋난다. → §4.5와 YAML을 `{rule_id: SEC-04, file: vulnerable/injection_test.py, verdict: confirmed}`로 확정한다.

**B3. §4 표와 §5 YAML 사이 누락 3건.**
① `secrets.ts`는 표에서 SEC-01/04 두 룰인데 YAML에는 SEC-01만 있다. ② P2는 표에서 `collect.py / collect.ts` 두 파일인데 YAML에는 collect.py만 있다. ③ SCA-03·04는 §3.1·§4.4 표에서 5종 발화인데 YAML에는 django 1건뿐이다. 대표 키잉을 의도했다면 "동일 룰의 예상외 발화는 오탐으로 세지 않는다"는 매칭 규칙(아래 M1)과 함께 명세에 명시해야 한다.

**B4. SCA-09~12의 오라클 키가 실제 방출 규약과 다르다 (§1.1).**
`sca_rules.py`를 대조하면: SCA-09는 **컴포넌트 단위로 `file=None`** 방출이며(`sca_rules.py:143-147`), lock 없는 pypi 환경에서는 매니페스트의 **전 컴포넌트에서 다발**한다(1건이 아니다). 따라서 YAML의 `{rule_id: SCA-09, file: vulnerable/requirements.txt}`는 어떤 finding과도 매칭되지 않는다. 반대로 SCA-10·11·12는 `file=declared_in`으로 방출되므로(`sca_rules.py:152-173`) §1.1이 SCA-11·12를 "file=None 그룹"에 넣은 분류가 틀렸다. → §1.1 표를 방출 규약대로 재작성하고, SCA-09는 대표 패키지 키잉 + 다발 허용으로 바꾼다.

**B5. §1.3 불변식의 적용 범위가 `vulnerable/`만으로는 부족하다.**
스캔은 API를 경유해 **저장소 전체**를 대상으로 하며(`measure_detection.py --api` 방식, Task 26 Step 3), 파이프라인에는 서브패스 한정 파라미터가 없다. 파일 키 룰은 측정 스크립트의 사후 필터로 범위를 좁힐 수 있지만, P8·P9·P10 같은 repo-wide 룰의 발화 조건은 이미 전체 트리에서 평가된 뒤라 사후 필터가 불가능하다. 예를 들어 `verification/measure_detection.py`에 `import logging` 한 줄이 있으면 P8이, `clean/query_safe.py`의 바인딩 예문에 `DELETE FROM`이 있으면 P10이 마스킹된다. → 불변식을 "저장소의 모든 코드 파일(clean/·verification/ 포함)"로 확장하고, §1.1 보정 ②의 "스캔 범위 한정"은 "매칭 시 사후 필터 + 저장소 전체 불변식"으로 정정한다.

### 메이저 — 측정 신뢰성에 직접 영향

**M1. 예상외 발견(unexpected findings)의 처리 규칙이 없다.**
SCA-03·04의 나머지 4종, SCA-09 다발, P4가 `collect.ts`에서 추가 발화할 가능성(fetch + PII 필드 조합), clean/ 파일의 import가 유발하는 SCA-01 등, 오라클에 없는 confirmed가 vulnerable/ 쪽에서 여러 건 나온다. 현행 정의(TPR = 검출/기대, FPR = clean/의 confirmed/파일 수)로는 이들이 어느 지표에도 잡히지 않는다. → 규칙을 명시한다: "vulnerable/에서 발생한 오라클 외 발견은 TPR·FPR에 세지 않되, 측정 리포트에 '부가 발견' 목록으로 공개한다."

**M2. 미선언 import가 의도치 않은 SCA-01을 낳는다.**
`crawler.py`의 `bs4`는 `beautifulsoup4`로 정규화되는데(`repo_checks.py:16`) §3.1 매니페스트에 선언이 없어 의도치 않은 SCA-01이 발생한다. `server.js`의 express·cors, `sqli.js`의 DB 드라이버도 같은 문제가 있다. → 불변식을 추가한다: "vulnerable/·clean/의 모든 비표준 import는 매니페스트에 선언하거나, 의도된 SCA-01 케이스로 오라클에 등재한다." stdlib은 자동 제외되므로(`imports_py.py:29`) 무관하다.

**M3. clean/ 파일은 stdlib만 쓰도록 강제한다.**
`secure_store.py`의 bcrypt·AES 서술대로 구현하면 bcrypt·cryptography가 미선언 SCA-01이 된다. 해시는 `hashlib`, 암호화 예시는 stdlib 조합으로 대체하면 M2 불변식을 자동으로 충족한다.

**M4. Flask 0.12.2의 "Low(비기여 검증)" 기대는 성립하지 않을 가능성이 높다.**
CVE-2018-1000656은 NVD 기준 CVSS 7.5(High)이고 Flask 0.12.2에는 CVE-2019-1010083(High)도 걸린다. OSV 스냅샷에서 Low로 나올 가능성은 낮다. → Low 등급의 "비기여" 검증은 이미 SCA-05(six, Low)가 담당하므로 Flask 행의 기대 severity를 "High(주의 기여)"로 정정하거나, 별도의 Low 전용 핀을 스캐폴딩 시점에 OSV로 선별한다.

**M5. SEC 계열의 line 키잉과 YAML 스키마가 어긋난다.**
§1.1은 SEC를 `(rule_id, file, line)`으로 키잉한다고 했지만 §5 YAML에는 line 필드가 없다. 라인은 스캐폴딩 전에는 알 수 없으므로 절차를 명시한다: "기획은 `(rule_id, file, verdict)`까지 확정하고, line은 스캐폴딩 직후 개발이 기입하되 rule_id·file·verdict는 변경하지 못한다." 매칭 자체는 `(rule_id, file)`로 완화해도 오라클 상 충돌이 없다(같은 파일·같은 룰 중복 기대가 없다).

**M6. P4·P7 fire-condition의 침범 방지 불변식이 빠졌다.**
P4는 `requests.post|fetch(|axios.`가 트리거이므로 이 호출은 `third_party.py`에만 두고, `collect.py`·`collect.ts`·`crawler.py`에서는 금지해야 P4가 예상 파일에서만 발화한다. P7은 파일 안에 `authenticate`·`@auth` 등 인증 단어가 주석으로라도 있으면 마스킹되므로(`repo_checks.py:54-55`) admin 파일 불변식에 추가한다.

### 마이너

- **m1.** §5의 `negatives_expect_no_confirmed: - vulnerable/../clean/` 경로 표기를 `clean/`으로 고친다.
- **m2.** 서문은 `[stretch]` 케이스를 언급하지만 §4 표에는 stretch로 표시된 행이 하나도 없다. 표시를 제거하거나 실제 stretch 행을 추가한다(고도화 항목 WP-6 참조).
- **m3.** AGPL·라이선스 불명·lock 불일치의 구체 패키지를 후보와 함께 확정한다. AGPL 후보: `PyMuPDF`(AGPL-3.0, 메타데이터 신뢰 가능). 불명·불일치는 스캐폴딩 시 메타데이터를 실측해 선정하고 YAML 플레이스홀더를 치환한다.
- **m4.** TPR·FPR 공식과 목표치 부재를 명세에 명시한다. 공식은 Task 26 Interfaces의 정의를 재인용하고, TDD가 수치 목표 없이 "측정·공개"만 요구함을 함께 적어 기대치를 고정한다.

## 3. PR 리뷰 포인트 7건에 대한 답변 초안

| # | 리뷰 포인트 | 답변 |
| --- | --- | --- |
| 1 | 취약점 목록 전체 승인 | **조건부 승인** — B1~B5 반영한 v0.2 커밋 후 게이트 통과 |
| 2 | 오라클 키 차등화 + measure_detection 보정 2건 | 패키지 키잉은 승인. 단 SCA-09~12 키는 B4대로 정정하고, "스캔 범위 한정"은 사후 필터 + 전체 저장소 불변식으로 대체(B5) |
| 3 | P8·P9·P10 FPR을 PyGoat·dogfooding으로 측정 | **승인** — 코드 구조상 같은 트리에 음성 공존이 불가능함을 확인했다 |
| 4 | 등급 재현성 트레이드오프(P1·P4 TPR 보류) | **전제 정정 필요** — P1·P4 초안은 정적 합성이라 키 없이도 TPR 측정 가능(B1). 등급의 static 재현성 주장 자체는 유효 |
| 5 | AUX-03 CORS 유지 vs 교체 | **유지 권고** — JS 룰이 실재하고 케이스가 명확하다. XSS·SSRF는 카탈로그 31종에 없어 교체가 성립하지 않는다 |
| 6 | CVE 5핀 severity·구체 패키지명 | OSV 스냅샷 확정 방식은 승인. 단 Flask Low 기대는 M4대로 재설계, AGPL 등은 m3 후보로 확정 |
| 7 | RRN 무효 = review_needed | **재확인 완료** — `pii.py:15` 상수와 주석이 명세와 일치한다 |

## 4. 고도화 계획 — 서브에이전트 작업 패키지

실행은 별도 모델의 서브에이전트가 담당한다는 전제로, 각 패키지를 독립 프롬프트로 넘길 수 있게 목표·입력·산출물·완료 기준을 분리했다. WP-1·2가 기획 게이트를 닫고, WP-3~5가 Task 26을, WP-6이 선택 고도화를 담당한다.

### WP-1. 명세 v0.2 개정 (블로커 해소) — 문서 작업, 선행 없음

- **목표**: `docs/benchmark-spec.md`를 B1~B5·M1~M6·m1~m4 반영판으로 개정하고 PR #12 브랜치(`docs/benchmark-spec`)에 커밋한다.
- **입력**: 이 문서 §2·§3, 현행 명세 v0.1, 인용된 엔진 코드.
- **산출물**: v0.2 명세(§1.1 방출 규약 표 재작성, §1.3 불변식 범위 확장 + M2·M6 불변식 추가, §1.4·§4.2 P1·P4 서술 정정, §4.5·§5 YAML의 SEC-04 확정과 누락 3건 보충, §5 경로 표기 수정, 매칭·부가 발견 규칙 절 신설).
- **완료 기준**: §4 표의 모든 행이 §5 YAML과 1:1 대응하고, 플레이스홀더는 m3에서 확정한 항목 외에 남지 않는다.
- **주의**: 순환 검증 회피 원칙 유지 — 룰 코드는 절대 수정하지 않는다. 개정은 오라클을 코드의 "현행 방출 규약"에 맞추는 것이지, 코드를 목록에 맞추는 것이 아니다.

### WP-2. 매칭 의미론 부록 — WP-1과 병행 가능

- **목표**: 측정이 기계적으로 재현되도록 오라클 매칭 규칙을 표로 확정한다.
- **산출물**: 명세 부록 "매칭 규칙" — 룰별 키(§1.1 정정판 기준), 다발성 룰(SCA-02·03·04·09, P7)의 대표 키잉과 중복 처리, 예상외 발견의 '부가 발견' 분리 공개(M1), TPR·FPR 공식과 분모 정의(m4), SEC line 기입 절차(M5).
- **완료 기준**: 이 표만 보고 measure_detection.py의 매칭 로직을 구현할 수 있다.

### WP-3. ansim-benchmark 스캐폴딩 + 불변식 CI — WP-1·2 승인 후

- **목표**: Task 26 Step 2를 v0.2 명세대로 수행하되, 불변식을 문서가 아니라 **자동 검사로 강제**한다.
- **산출물**: `ansim-benchmark` 공개 저장소(vulnerable/·clean/·verification/·README) + `verification/check_invariants.py`: ① 전 코드 파일에서 `import logging`·winston·pino 부재 ② privacy 파일명·라우트 부재 ③ 삭제 동사 부재 ④ 모든 import의 매니페스트 선언 여부(의도된 SCA-01 예외 목록 대조) ⑤ P4 트리거 호출이 third_party.py 밖에 없는지 ⑥ 인증 단어가 admin 파일에 없는지를 검사하고, 위반 시 비영(non-zero)으로 종료한다. GitHub Actions로 push마다 실행한다.
- **완료 기준**: check_invariants 통과 + 명세 §4의 모든 행이 파일·라인 하나에 대응 + line 값이 YAML에 기입됨(M5 절차).
- **비고**: 이 자동 검사가 이번 고도화의 핵심이다. 벤치마크 저장소를 나중에 수정할 때 repo-wide 양성이 조용히 마스킹되는 회귀를 구조적으로 차단한다.

### WP-4. measure_detection.py 구현 — WP-2 완료 후, WP-3과 병행 가능

- **목표**: Task 26 Step 3의 측정 스크립트를 WP-2 매칭 규칙대로 구현한다.
- **산출물**: `verification/measure_detection.py` — API 스캔 호출 → finding 회수 → 사후 필터(vulnerable/·clean/ 외 경로 제외, repo-wide 룰은 예외) → 룰별 키 매칭 → TPR·FPR·부가 발견 3단 표 생성 → `docs/measurements.md` append 형식 출력.
- **완료 기준**: 오라클 YAML만 바꿔도 재실행이 되는 순수 함수형 매칭 + 부가 발견이 표에 분리 표기 + **fail-closed 검사**: 오라클에 미기입 센티넬(`TBD`인 SCA-08 패키지명, SEC 계열의 빈 `line`)이 남아 있으면 측정을 진행하지 않고 에러로 중단한다(PR #12 리뷰에서 작성자가 수락한 비차단 제안 — "값 불일치 → 조용한 TPR 0" 계열을 구조적으로 차단).

### WP-5. 측정 실행과 기록 — WP-3·4 완료 후

- **목표**: TPR·FPR 실측, P8·P9·P10 FPR의 PyGoat·dogfooding 측정(승인된 리뷰 포인트 3), Flask severity의 OSV 스냅샷 확정(M4)과 YAML 잔여 플레이스홀더 치환(m3).
- **산출물**: `docs/measurements.md` 표(31종 전체, 미시연 룰 포함 — TDD §9 ③), FPR>0 룰의 allowlist 보정 1회 반영 기록.
- **완료 기준**: Task 26 DoD 충족 + 등급 시나리오 태그 3종(v1-danger·v2-warning·v3-safe)이 §7 시나리오대로 재현.

### WP-6. 선택 고도화 — 일정 여유 시

- **stretch 케이스 세트**(m2): base64 인코딩 시크릿, 여러 줄에 걸친 SQL 조립, ORM raw 쿼리 등 현행 룰이 놓칠 만한 변형을 `[stretch]` 표시와 함께 추가해 룰 갭 신호를 실측한다. 미검출을 결함이 아니라 갭 신호로 기록하는 원칙을 measurements.md 서식에 반영한다.
- **인젝션 페이로드 확장**(Task 27 연계): 주석 지시문 변형(영어·역할 사칭·JSON 위장) 2~3종을 추가해 G3 구조 방어를 다각도로 시연한다.

### 실행 순서와 의존성

```
WP-1 ─┬─> (기획 승인 게이트: PR #12 머지) ─> WP-3 ─┬─> WP-5 ─> WP-6(선택)
WP-2 ─┘                                    WP-4 ─┘
```

WP-1·2는 문서 작업이라 즉시 착수할 수 있고, PR #12 머지가 곧 M7 게이트 통과다. WP-3·4는 병행 가능하며 WP-5가 합류 지점이다. 마감(08-30 목표 완료) 압박 시 포기 순서는 WP-6 → stretch 없이 WP-5까지가 MVP 경계다.
