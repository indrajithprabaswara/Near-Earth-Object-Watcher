# Near-Earth Object Watcher

This app periodically ingests NASA's NEO feed and exposes a small dashboard with real time charts. Close approaches under 0.05 AU trigger Slack notifications. All code runs with FastAPI and a Postgres database.

## Local development

```bash
# start app and database with hot reload
NASA_API_KEY=demo-key SLACK_URL=http://localhost \
  docker-compose -f docker-compose.yml -f docker-compose.override.yml up --build
```

The app will be available on [http://localhost:8080](http://localhost:8080). Any code change automatically reloads the server.

### Running tests

```bash
pip install -r requirements.txt
npm ci
pytest --cov
```

Playwright UI tests run via `npx playwright test`.

## Docker usage

To build and run the production container manually:

```bash
docker build . -t neo-watcher:final
docker run --rm -p 8080:8080 neo-watcher:final
```

Health and metrics endpoints are exposed at `/health` and `/metrics`.

## CI/CD pipeline

GitHub Actions lint, type-check and run the full test suite. On success the workflow performs Terraform `plan` and `apply` followed by a Cloud Run deploy:

```bash
terraform init
terraform plan
terraform apply --auto-approve

gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
gcloud run deploy neo-watcher --source . --no-promote --region=us-central1 --platform=managed
```

A service account key is provided via repository secrets.

### Deploy and rollback

Deploys are triggered automatically from CI but can be run locally with the commands above. To rollback simply redeploy a previous container tag using `gcloud run deploy` with the desired image.

## Monitoring

Prometheus scrapes `/metrics` and Grafana dashboards visualise request counts and latencies. Configure your Prometheus server to scrape the running service on port 8080.

## Troubleshooting

- **Container fails to start** – ensure database connection variables are correct and the Postgres service is reachable.
- **Tests fail locally** – run `npm ci` to install frontend dependencies before executing Playwright tests.
- **Terraform errors** – verify that the Google credentials have permissions for Cloud Run and that the Cloud SDK version matches the API.

