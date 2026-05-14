# Target Architecture

## User-facing language

- Vietnamese
- Mixed Vietnamese/English
- Casual, short, incomplete phrases

## Internal language

- English prompts
- English action schema
- English workflow and reasoning labels

## Core services

1. Telegram webhook ingress
2. Message normalization and media extraction
3. Memory retrieval
4. AI intent and entity extraction
5. Workflow execution
6. Google Sheets / business system write
7. Audit log and monitoring
8. Response generation

## Storage design

- PostgreSQL: users, conversations, actions, workflow logs
- Redis: short-term session state, dedupe, rate limit, cache
- Vector DB: semantic memory and retrieval for prior entities

## AI model strategy

- Primary: OpenAI for structured tool calling and multilingual reasoning
- Fallback: Claude for conversational resilience and backup routing
- OCR/STT: model-selected by task type

## Business domains

- Expenses
- Tasks
- Inventory
- Revenue
- Travel
- CRM
- General notes

## Guardrails

- Require follow-up question only when a write action is ambiguous
- Log every mutation with before/after payload
- Keep user responses concise and natural
- Separate extraction confidence from execution confidence

