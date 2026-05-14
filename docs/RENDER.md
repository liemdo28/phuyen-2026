# Render Deployment

This project can run on Render as a Docker-based FastAPI webhook service for Telegram.

## Why Render

- no Google Cloud billing setup required
- simpler first deploy than Cloud Run
- works well for a Telegram webhook MVP

## Important Notes

- Render web services must bind to the `PORT` environment variable
- this repo's Dockerfile already supports that
- free usage on Render is limited and may spin down between requests
- avoid aggressive keep-alive pings if you want to preserve free usage

## Create The Web Service

1. Go to Render Dashboard
2. Click `New` -> `Web Service`
3. Connect GitHub repo `liemdo28/phuyen-2026`
4. Use these settings:
   - Environment: `Docker`
   - Branch: `main`
   - Instance Type: your lowest-cost or free-eligible option

## Required Environment Variables

Set these in the Render service:

- `APP_ENV=production`
- `QUEUE_BACKEND=inline`
- `TELEGRAM_BOT_TOKEN=...`
- `TELEGRAM_WEBHOOK_SECRET=...`

Optional:

- `OPENAI_API_KEY=...`
- `ANTHROPIC_API_KEY=...`
- `DEFAULT_SPREADSHEET_ID=...`
- `GOOGLE_SERVICE_ACCOUNT_JSON=...`

## Verify Health

After deploy, Render gives you a public URL like:

```text
https://phuyen-2026.onrender.com
```

Open:

```text
https://YOUR-RENDER-URL/health
```

Expected:

```json
{"status":"ok","env":"production"}
```

## Register Telegram Webhook

Use `curl` with the real token, service URL, and webhook secret:

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://YOUR-RENDER-URL/api/telegram/webhook" \
  -d "secret_token=<WEBHOOK_SECRET>"
```

Then verify:

```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

Healthy signs:

- `ok: true`
- webhook URL points to Render
- no `last_error_message`
- low `pending_update_count`

## Expected Runtime Behavior

- `/start` returns the welcome message
- `/id` returns the Telegram user id
- natural Vietnamese text routes through the AI workflow layer

## Known Limitations

- `QUEUE_BACKEND=inline` is acceptable for MVP only
- in-memory / SQLite-style persistence is not ideal for multi-instance production
- free-tier cold starts may affect webhook latency

## Recommended Next Upgrade

After Render is stable:

1. add Redis-backed queueing
2. add Postgres persistence
3. add real Google Sheets adapter
4. add structured LLM extraction
