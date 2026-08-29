FROM zricethezav/gitleaks:v8.18.4 AS gitleaks
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
COPY --from=gitleaks /usr/bin/gitleaks /usr/local/bin/gitleaks
WORKDIR /srv
# 빌드 컨텍스트는 저장소 루트(docker-compose.yml의 context: .) — rules/·data/를 이미지에 동봉하기 위해서다.
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api/app ./app
COPY rules /srv/rules
COPY data /srv/data
# uvicorn 단일 워커 고정 (TDD §4.1 — BackgroundTasks in-process 전제)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
