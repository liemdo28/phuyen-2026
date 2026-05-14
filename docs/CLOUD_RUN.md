# Cloud Run Deployment

This project can move Telegram webhook handling off Apps Script and onto Cloud Run.

## What This Solves

- avoids the Apps Script `302 Moved Temporarily` webhook problem
- gives Telegram a stable HTTPS webhook endpoint that returns `200 OK`
- keeps the Vietnamese-first FastAPI backend as the main bot runtime

## Current Production Scope

The Cloud Run service in this repo currently supports:

- Telegram webhook receive at `/api/telegram/webhook`
- direct Telegram reply via Bot API
- Vietnamese heuristic NLU and workflow routing
- local SQLite persistence inside the container revision

It does **not** yet provide durable production queueing or durable multi-instance storage. For initial rollout, use:

- `QUEUE_BACKEND=inline`
- Cloud Run `min-instances=0`
- modest traffic only

## Prerequisites

1. A Google Cloud project with billing enabled
2. `gcloud` installed and logged in
3. Telegram bot token
4. Optional:
   - OpenAI API key
   - Anthropic API key
   - Google Sheets credentials

## Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

## Recommended Region

Use `asia-southeast1` for Vietnam/Southeast Asia latency.

## Deploy

From the repo root:

```bash
gcloud run deploy phuyen-telegram-ai \
  --source . \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 3 \
  --set-env-vars APP_ENV=production,APP_PORT=8080,QUEUE_BACKEND=inline
```

After the first deploy, update env vars with your real values:

```bash
gcloud run services update phuyen-telegram-ai \
  --region asia-southeast1 \
  --update-env-vars TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN,TELEGRAM_WEBHOOK_SECRET=YOUR_SECRET,OPENAI_API_KEY=YOUR_OPENAI_KEY,DEFAULT_SPREADSHEET_ID=YOUR_SHEET_ID
```

If you need to pass service-account JSON directly:

```bash
gcloud run services update phuyen-telegram-ai \
  --region asia-southeast1 \
  --update-env-vars GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"..."}'
```

## Get The Service URL

```bash
gcloud run services describe phuyen-telegram-ai \
  --region asia-southeast1 \
  --format='value(status.url)'
```

Your webhook URL will be:

```text
https://YOUR_CLOUD_RUN_URL/api/telegram/webhook
```

## Set Telegram Webhook

Telegram supports a webhook secret header. This repo already validates:

- `X-Telegram-Bot-Api-Secret-Token`

Set the webhook:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -d "url=https://YOUR_CLOUD_RUN_URL/api/telegram/webhook" \
  -d "secret_token=YOUR_SECRET"
```

Check webhook health:

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

Healthy signs:

- no `last_error_message`
- low `pending_update_count`
- webhook URL points to Cloud Run, not Apps Script

## Test Endpoints

Health check:

```bash
curl "https://YOUR_CLOUD_RUN_URL/health"
```

Expected:

```json
{"status":"ok","env":"production"}
```

## First Production Test Plan

1. Send `/start`
2. Send `/start` again after a few seconds
3. Send `/id`
4. Send a normal Vietnamese message like `thêm bill điện 2tr6`
5. Run `getWebhookInfo` and confirm no webhook delivery errors

## Cost Expectation

For a small Telegram bot, Cloud Run is likely to stay within the always-free tier if traffic is moderate. The bigger cost risks are usually:

- OpenAI / Anthropic usage
- managed Redis / Postgres later
- network egress if traffic becomes large

Official pricing:

- https://cloud.google.com/run/pricing

## GitHub Actions Auto Deploy

This repo now includes a dedicated workflow:

- `.github/workflows/cloud-run.yml`

It deploys to Cloud Run automatically on pushes to `main` when backend-related files change.

### Required GitHub Variables

Create these in:

- `Repo -> Settings -> Secrets and variables -> Actions -> Variables`

Variables:

- `GCP_PROJECT_ID`
- `CLOUD_RUN_SERVICE`
- `CLOUD_RUN_REGION`
- `OPENAI_MODEL`
- `ANTHROPIC_MODEL`

Suggested values:

- `CLOUD_RUN_SERVICE=phuyen-telegram-ai`
- `CLOUD_RUN_REGION=asia-southeast1`
- `OPENAI_MODEL=gpt-4.1-mini`
- `ANTHROPIC_MODEL=claude-3-5-sonnet-latest`

### Required GitHub Secrets

Create these in:

- `Repo -> Settings -> Secrets and variables -> Actions -> Secrets`

Required:

- `GCP_SA_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`

Optional:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `DEFAULT_SPREADSHEET_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON`

### What `GCP_SA_KEY` Should Be

Use a Google Cloud service account JSON key with permissions for Cloud Run deploys.

At minimum, the service account should be able to:

- deploy Cloud Run services
- run Cloud Build
- write to Artifact Registry

In practice, many teams start with:

- `Cloud Run Admin`
- `Cloud Build Editor`
- `Artifact Registry Writer`
- `Service Account User`

### First-Time Setup Flow

1. Create the service account in Google Cloud
2. Generate its JSON key
3. Save the entire JSON as GitHub secret `GCP_SA_KEY`
4. Add the GitHub variables and other secrets above
5. Push to `main` or trigger `workflow_dispatch`

### After Auto Deploy

When the workflow succeeds, it prints the deployed Cloud Run URL in the Actions summary.

Then set Telegram webhook to:

```text
https://YOUR_CLOUD_RUN_URL/api/telegram/webhook
```

## Important Current Limitations

- `QUEUE_BACKEND=inline` is acceptable for MVP rollout, not ideal for long AI jobs
- SQLite inside Cloud Run is not durable across revisions/instances
- Redis / Postgres / vector memory should be added for full production hardening

## Recommended Next Upgrade

After Cloud Run webhook is stable:

1. move queue to Redis
2. move persistence to Postgres
3. add Google Sheets real adapter
4. add OpenAI structured extraction
