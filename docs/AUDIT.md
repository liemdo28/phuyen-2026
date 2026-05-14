# Telegram AI System Audit

Date: 2026-05-14

## Executive summary

The current implementation in [Code.js](/Users/liemdo/phuyen-2026/Code.js:1) is a useful Google Apps Script travel-and-expense bot, but it is not yet a production AI assistant. It is tightly coupled to a single spreadsheet, depends on regex keyword routing, has no persistent multi-turn memory, and cannot safely support broad business workflows without a dedicated backend.

## Critical gaps against CEO requirements

1. Natural language understanding is rule-based.
   Current message handling in [Code.js](/Users/liemdo/phuyen-2026/Code.js:865) routes by regex and fixed commands, which directly conflicts with the requirement that users should not need commands or fixed syntax.

2. No true context memory.
   The bot does not maintain entity-aware memory for references like "cái trên", "task này", or "thêm 500k nữa". It only stores location in script properties and recently added a duplicate webhook guard.

3. Single-domain business logic.
   The spreadsheet and parser are centered on travel expenses, packing lists, and restaurant suggestions. There is no generalized engine for tasks, inventory, revenue, CRM, or cross-sheet action routing.

4. No production AI orchestration layer.
   There is no OpenAI/Claude orchestration, confidence scoring, fallback model routing, or prompt logging. OCR currently depends on a single Gemini prompt inside Apps Script.

5. No durable backend infrastructure.
   Apps Script is not sufficient for the stated production goals involving async webhooks, Redis, Postgres, vector memory, observability, and extensible integrations.

6. Weak operational observability.
   There are no structured action logs, no monitoring pipeline, no failed-intent capture, and no audit trail for business writes.

## What was fixed immediately

1. Duplicate Telegram updates are now ignored in [Code.js](/Users/liemdo/phuyen-2026/Code.js:839), preventing repeated replies when Telegram retries a webhook.
2. Lightweight commands now fetch the Telegram token through a cache-first path in [Code.js](/Users/liemdo/phuyen-2026/Code.js:803), reducing config-sheet reads and improving `/start` and `/id` responsiveness.

## Production path created in this repo

A new FastAPI backend scaffold was added under [backend](/Users/liemdo/phuyen-2026/backend) to become the real AI execution layer. It introduces:

- Telegram webhook API
- Vietnamese NLU service with English internal orchestration
- Context memory service
- Workflow engine for create/update/query/delete routing
- Google Sheets adapter abstraction
- Voice/OCR adapter stubs
- Internal English system prompt

## Recommended rollout

1. Keep Apps Script running as the temporary production bot for the trip workflow.
2. Stand up the FastAPI backend and connect it to Telegram in a staging bot.
3. Replace in-memory adapters with real OpenAI, Redis, Postgres, vector DB, and Google Sheets APIs.
4. Migrate one domain at a time: expenses first, then tasks, inventory, and revenue.
5. Add observability before enabling write actions broadly.

