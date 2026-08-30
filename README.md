# 안심코드(AnsimCode)

> 전 국민 앱 개인정보 검사소 — 2026 ICT 표준 챌린지 공모전 데모

생성형 AI 바이브코딩으로 만들어진 앱의 소스코드를 **TTA 표준 4종의 조항 단위로 자동 진단**하는 웹 서비스다. 공개 git URL이나 zip을 올리면 표준 조항에서 도출한 진단 룰 31종으로 검사하고, 발견 사항마다 **근거 조항·코드 위치·수정 프롬프트**를 제시한다. 개발자용 조항 인용 리포트와 시민용 쉬운 한국어 설명, 공개 안전등급(안심·주의·위험)을 함께 제공한다.

## 근거로 삼는 표준

| 표준 | 이름 | 구현 대상 |
| --- | --- | --- |
| TTAK.KO-11.0259/R1 | 오픈소스 소프트웨어 보안취약점 관리 지침 | 진단 파이프라인 5단계, 안전등급(§11.3 위험 평가 지수) |
| TTAK.KO-11.0309/R1 | SBOM 속성 규격 | 15속성 SBOM 생성·출력 |
| TTAK.KO-11.0322 | 오픈소스 SBOM 거버넌스 관리 지침 | 공급망 환경 분류, 비즈니스 모델별 위험요인 매트릭스 |
| TTAK.KO-12.0414 | AI 서비스 개인정보보호 프레임워크 | 개인정보 생명주기 진단 룰 10종 |

## 문서

설계·결정·실행 문서는 [`docs/`](docs/index.md)에 있다. Open Knowledge Format v0.2 번들로 구성되어 있어 사람과 에이전트가 같은 파일을 읽는다.

- [문서 색인](docs/index.md) — 번들 진입점
- [TDD](docs/tdd.md) — 설계 명세 (아키텍처·룰 카탈로그·등급 결정론·보안)
- [ADR-001](docs/platform-decision.md) — 플랫폼 선정 결정과 근거
- [MVP 구현 계획](docs/plans/mvp-implementation.md) — 7 마일스톤 28 태스크
- [TTA 표준 원문](docs/references/index.md) · [조항 색인](docs/references/clause-index.md)

## 기술 구성

React 18 + TypeScript(Vite, nginx 서빙) / FastAPI + Python 3.12 / PostgreSQL 16 / Semgrep CE + gitleaks(자체 룰 전용) / OSV.dev API + KISA 보호나라 스냅샷 / Anthropic Claude API. 로컬 Docker Compose 3서비스로 기동한다.

원본 소스코드는 스캔별 격리 디렉토리에서만 존재하고 `try/finally`로 무조건 파기된다 — 이 정책 자체가 TTAK.KO-12.0414 §7.3.5(지체 없는 파기)의 자기 적용이다.

## 실행

로컬 Docker Compose 3서비스(db·api·web)로 기동한다. `.env`가 없으면 compose가 뜨지 않는다.

```bash
cp .env.example .env
```

`.env`의 `ANTHROPIC_API_KEY`에 실제 Anthropic 키를 채운다 — 비어 있어도 스캔은 끝까지 돌지만 LLM 판정과 시민용 변환 단계는 건너뛴다.

```bash
docker compose up -d --build
```

데모 진입점은 <http://localhost:8080>이고 API는 <http://localhost:8000>에서 직접 열린다(`/health`·`/docs`). 8080이 점유된 경우에만 `WEB_PORT`로 덮어쓴다. 첫 기동 때 진단 룰 31종이 DB에 시드된다. 종료는 `docker compose down`, 스키마를 갈아엎을 때는 `-v`를 붙인다.

## 개발

api 테스트는 compose 네트워크의 PostgreSQL을 쓰므로 컨테이너 안에서 돌린다(테스트 DB `ansim_test`는 자동 생성된다).

```bash
docker compose run --rm -v "$PWD:/work" -w /work/api api pytest
```

```bash
cd web && npm ci && npm run build
```

## 도구

```bash
python3 tools/okf_check.py docs
```

`docs/` 번들의 OKF v0.2 적합성(frontmatter 파싱·`type` 존재·예약 파일 구조)과 문서 간 링크·조항 앵커를 점검한다.

## 고지

안심코드의 안전등급은 **인증이 아닌 자가점검 보조**다.
