You are a senior Python full-stack engineer. In ONE SHOT, generate a full “Near-Earth Object Watcher” project that meets all 13 A-Level rubric items, hard-codes the NASA API key and Slack webhook, and then immediately runs every test and verifies every interface. The UI must be professional-grade, with smooth animations and advanced charts. Here are the requirements:

1. CONFIGURATION  
   - In your Python code, hard-code:
     ```python
     NASA_API_KEY = "MYMSkV14dmSN0l5eqyeF8OcAEClbH5jWw9JfYceM"
     SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/XXX/YYY/ZZZ"
     DATABASE_URL = "postgresql://postgres:password@db:5432/neo_watcher"
     ```
   - No `.env` or secret manager—everything lives in code for this exercise.

2. TECHNOLOGY STACK  
   - Backend: Python 3.9+, FastAPI, SQLAlchemy, Alembic migrations  
   - Database: PostgreSQL (local via Docker Compose; Cloud SQL on GCP)  
   - Frontend: HTML5, CSS3 (Flexbox/Grid, CSS animations), JavaScript (ES6+), Chart.js + D3.js for animated time-series, anime.js for UI transitions  
   - Real-time: Server-Sent Events endpoint at `/stream/neos`  
   - Alerting: Slack webhook for any NEO with `miss_distance_au < 0.05`  
   - Monitoring: Prometheus via `fastapi_prometheus`, Grafana dashboards  
   - Scheduling: APScheduler within FastAPI for daily ingest

3. FEATURES  
   - **Daily Ingest**: APScheduler job at 00:00 UTC calls  
     `https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_API_KEY}`  
   - **Data Normalization**: Extract diameter, velocity, miss_distance; store raw + enriched in PostgreSQL  
   - **REST API**:  
     - `GET /neos?start_date=&end_date=&hazardous=`  
     - `GET /neos/{id}`  
     - `POST /subscribe` (stores subscriber URLs for alerts)  
   - **SSE**: `GET /stream/neos` pushes JSON for each newly ingested NEO  
   - **Frontend**:  
     - Responsive dashboard with:  
       • Animated Chart.js time-series (daily counts, min distances)  
       • D3.js force-directed “danger zone” map of close-approach  
       • Live SSE overlay highlights new NEOs with CSS pop-ins  
       • Subscription form to register Slack/email alerts  
   - **Alert Microservice**: On ingest, POST payload to `SLACK_WEBHOOK_URL` for any NEO closer than 0.05 AU

4. DATA PERSISTENCE  
   - SQLAlchemy models + Alembic migrations under `alembic/`  
   - Docker Compose `db` service for local development

5. TESTING  
   - **Unit tests**: `pytest` & `pytest-asyncio` for business logic and routes  
   - **Integration tests**: `pytest` + `httpx.AsyncClient` against FastAPI TestClient for all REST & SSE endpoints  
   - **UI tests**: Playwright scripts to verify dashboard loads, charts animate, SSE updates stream, subscription form posts  
   - **Mocking**: Use `respx` to stub NASA API and `pytest-monkeypatch` to stub Slack calls

6. CI/CD  
   - **GitHub Actions** (`.github/workflows/ci.yml`):  
     1. Checkout code, install deps, run linters (flake8, black), type-check (mypy)  
     2. Execute unit + integration + UI tests  
     3. Build Docker images and push to GitHub Container Registry  
     4. Run `terraform plan` & `terraform apply` on GCP (Cloud Run, Cloud SQL, Secret Manager)  
     5. Deploy with `gcloud run deploy neo-watcher --source .`

7. MONITORING & PRODUCTION  
   - Instrument FastAPI with OpenTelemetry, expose `/metrics`  
   - Terraform modules to provision Prometheus, Grafana on GCP, and scrape the service  
   - Grafana alerts on high error rates and ingest latency > 60 s

8. DELIVERY & VERIFY  
   - Provide `Dockerfile`, `docker-compose.yml`, Terraform modules, GitHub workflows, and a comprehensive `README.md`  
   - At the end of generation, automatically run:
     ```
     pip install -r requirements.txt
     pytest --cov
     npm install -g playwright && playwright install --with-deps
     pytest integration_tests/
     playwright test
     terraform init && terraform validate
     docker-compose up --build --detach
     gcloud auth login && gcloud run deploy neo-watcher --source .
     ```
   - Verify 100% test coverage, all REST & SSE endpoints, UI flows (animated charts, maps, live feed), and Slack alerts trigger for a mock NEO with `miss_distance_au < 0.05`.

Generate all code, infra, configs, then run all tests and interface checks in one shot. Use your maximum time. 
