# Agent Instructions — 안심코드(AnsimCode)

TTA ICT 챌린지 출품 데모. 웹 플랫폼 + 보안 강화 방향, 로컬 Docker Compose 3서비스(`db`/`api`/`web`)로만 기동한다.

## 스택

- `api/` — FastAPI + Python 3.12, 의존성은 `api/requirements.txt` (pip)
- `web/` — React 19.2 + TypeScript + Vite, 패키지 매니저는 **npm** (`web/package-lock.json`)
- LLM은 Anthropic Claude API. 모델 ID는 `api/app/config.py`의 `judge_model`·`convert_model`

## Commands

기동·`.env` 설정·전체 테스트·`okf_check`는 `README.md`의 「실행」·「개발」·「도구」를 따른다. 아래는 거기 없는 파일 단위 명령이다. `web` 항목 외에는 저장소 루트에서 실행한다.

| Task | Command |
|------|---------|
| API 테스트 1개 파일 | `docker compose run --rm -v "$PWD:/work" -w /work/api api pytest tests/test_pii.py -v` |
| 룰 변경분까지 반영한 테스트 | 위 명령에 `-e RULES_DIR=/work/rules` 추가 |
| 프론트 린트 1개 파일 | `cd web && npx oxlint src/pages/Home.tsx` |
| 프론트 개발 서버 | `cd web && npm run dev` |

## External References

설계 내용을 이 파일에 복제하지 말고 아래를 읽는다.

| Need | File |
|------|------|
| 기동·환경 변수·데모 진입점 | `README.md` |
| 설계 전반(아키텍처·등급 결정론·보안) | `docs/tdd.md` |
| 플랫폼 선정 결정과 근거 | `docs/platform-decision.md` |
| 구현 계획·태스크별 DoD | `docs/plans/mvp-implementation.md` |
| 문서 번들 목차 | `docs/index.md` |
| 실측·이슈 검증 기록 | `docs/measurements.md` |
| 벤치마크 취약점 목록(룰 TPR·FPR 측정) | `docs/benchmark-spec.md` |
| TTA 표준 원문 / 조항 색인 | `docs/references/index.md` · `docs/references/clause-index.md` |
| 진단 룰 31종의 단일 사양 | `rules/catalog.yaml` |

## Key Conventions

- 파일 편집은 Write/Edit 도구로 한다. Bash의 `sed`·heredoc 편집은 세션 백업의 변경 파일 목록에서 누락된다.
- `semgrep`·`gitleaks` 바이너리는 호스트에 없다. 이를 쓰는 테스트는 위 `docker compose run` 경로로만 검증된다.
- `rules/`·`data/`는 API 이미지에 구워진다(`api/Dockerfile`). 테스트에 `RULES_DIR`를 주지 않으면 이미지 안 `/srv/rules`를 읽으므로, 방금 고친 룰이 조용히 무시된다. 서비스에 반영하려면 `docker compose up -d --build api`.
- `rules/` 전체의 콘텐츠 해시가 `rule_catalog_version`이다. 룰 파일 변경은 버전 변경이며 재진단 diff에 영향을 준다.
- uvicorn 워커는 1로 고정한다. 파이프라인이 `BackgroundTasks` in-process를 전제한다.
- 원본 소스코드는 스캔별 격리 워크스페이스에만 존재하고 `try/finally`로 무조건 파기된다. 이 경로를 우회하는 변경 금지.
- `ANTHROPIC_API_KEY`는 `.env`로만 주입한다. 키를 코드·문서·로그에 넣지 않는다.
- `docs/` 문서는 OKF v0.2 번들이다. 문서를 추가·수정하면 YAML frontmatter를 유지하고 `tools/okf_check.py`로 확인한다.

## Commit Attribution

AI 커밋에는 트레일러를 붙인다:

```
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```
