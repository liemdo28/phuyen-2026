# Human Experience OS

This system is evolving beyond a bot into a human-centered intelligence layer.

## Philosophy

The AI exists to:

- reduce chaos
- reduce overload
- protect energy
- improve movement through the real world
- support recovery and calmness

The AI must not:

- maximize screen time
- manipulate emotion
- create addictive notification loops
- overwhelm the user with options

## New Backbone Layers

### `backend/app/ethics/`
Calm-technology policy:
- decides whether to interrupt
- caps option count
- selects safe surfaces such as:
  - `silent_background`
  - `passive_hint`
  - `chat_only`
  - `priority_alert`

### `backend/app/recovery/`
Recovery intelligence:
- converts fatigue/stress into a recovery plan
- estimates how much rest / simplification is needed
- protects physical, emotional, and decision energy

### `backend/app/society/`
Multi-agent society skeleton:
- `routing_ai`
- `weather_ai`
- `recovery_ai`
- `safety_ai`
- `exploration_ai`
- `orchestration_ai`

These agents do not act independently yet; they produce aligned guidance under calm-technology constraints.

## Existing Supporting Layers

- `travel_companion.py`: emotional state inference
- `travel_operating_system.py`: world model + energy + rhythm + local timing
- `travel_brain.py`: emotional + personalization + realtime provider fusion
- `semantic_memory.py`: vector-memory-ready abstraction

## Production Direction

```text
Telegram / Interfaces
    -> Webhook / Queue
    -> Orchestrator
    -> Travel Brain
    -> Calm Technology Policy
    -> Recovery Engine
    -> Agent Society
    -> Realtime Providers / Memory / Sheets / Maps / APIs
```

## Next Real Build Steps

1. Wire `TravelBrain` + `CalmTechnologyPolicy` + `RecoveryEngine` into the live reply composer
2. Add real providers:
   - weather
   - traffic/maps
   - local business activity
   - events
   - sea/beach conditions
3. Move session state to Redis
4. Move long-term profile + emotional memory persistence to PostgreSQL
5. Add semantic recall with a real vector DB
6. Add low-noise proactive nudges with strict interruption budgets

## UX Rule

If the AI is unsure whether to interrupt, it should choose silence.
