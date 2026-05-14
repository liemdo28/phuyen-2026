# Deployment Outline

## Phase 1

- Keep Apps Script bot active
- Deploy FastAPI backend to staging
- Register a separate Telegram staging bot webhook
- Connect OpenAI, Google Sheets, and logging first

## Phase 2

- Add Redis for dedupe and session memory
- Add Postgres for action logs and structured records
- Add vector memory for semantic recall
- Enable real OCR and STT providers

## Phase 3

- Shadow traffic from production messages
- Compare AI actions with human/admin expectations
- Turn on write actions domain by domain

## Minimum production checklist

- webhook secret validation
- request logging
- duplicate update protection
- structured action logs
- retry strategy for outbound Telegram API calls
- Google Sheets write audit trail
- confidence threshold for destructive actions

