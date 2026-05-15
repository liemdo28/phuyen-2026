# Travel OS Ecosystem

This backend is evolving from a Telegram bot into a production travel intelligence layer.

## Production Flow

```text
Local Development
    -> GitHub
    -> Auto Deploy
    -> Render Backend
    -> Google Apps Script
    -> Google Sheets / APIs
    -> Telegram AI System
```

## Core Runtime Layers

- `backend/app/services/travel_companion.py`
  Emotional inference and response shaping.
- `backend/app/orchestration/travel_operating_system.py`
  World model + energy + local intelligence + prediction + rhythm.
- `backend/app/orchestration/travel_brain.py`
  Higher-level decision engine that merges:
  - emotional memory
  - personalization
  - realtime provider signals
  - operating posture
- `backend/app/realtime/`
  Provider registry and live context normalization.
- `backend/app/memory/semantic_memory.py`
  Vector-memory-ready abstraction for future semantic recall.
- `backend/app/personalization/`
  Long-lived preference snapshots.
- `backend/app/emotional/`
  Emotional baselines and burnout-aware state.

## Current Capability Level

Phase 4 foundation is heuristic-first and production-safe:

- detects travel stress, fatigue, overwhelm, exploration energy
- models traffic/weather/local timing pressure from conversation context
- estimates low-friction vs expand-exploration posture
- reduces recommendation count when energy is low
- adds proactive travel guidance before the user asks follow-up questions

## Next Live Integrations

1. Weather provider with real API
2. Traffic / Maps provider with real ETAs
3. Local business activity provider
4. Event density provider
5. Beach / sea condition provider
6. Redis-backed session memory
7. PostgreSQL long-term profile persistence
8. Vector DB semantic recall

## Safety + UX Principles

- never spam proactive suggestions
- compress guidance when stress/fatigue is high
- prefer fewer options when decision energy is low
- bias toward comfort, simplicity, and lower travel friction
- keep recommendations local-feeling rather than tourist-generic
