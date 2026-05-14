# Production Hardening Status

## Implemented in repo

- Immediate webhook ACK path via queue abstraction
- Optional Redis queue backend with worker entrypoint
- Persistent SQLite conversation/entity/action storage
- SQLite-backed loop guard for dedupe and retry protection
- Bot-message ignore logic
- Rate limiting and repeated-text suppression
- Sheet mapping abstraction for multi-domain Google Sheet actions
- Docker Compose scaffold with API, worker, and Redis

## Still required before calling this fully production-ready

- Real Redis deployment in production
- Real PostgreSQL / pgvector or Qdrant for memory retrieval
- Real Google Sheets OAuth adapter
- Real Telegram outbound adapter
- OpenAI / Claude production structured output and fallback logic
- OCR provider integration
- Admin dashboard and alerting

## Recommended next rollout

1. Run `docker compose up` in staging.
2. Move queue backend to Redis in staging.
3. Replace SQLite persistence with Postgres once data model stabilizes.
4. Add real Google Sheets row read/write adapter.
5. Add provider fallback and token accounting.
