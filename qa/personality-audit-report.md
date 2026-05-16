# Mi Personality Audit Report
**Date:** 2026-05-16  
**Auditor:** Dev Team (Claude Code)  
**Service:** phuyen-2026-telegram.onrender.com  

---

## 1. Personality Loaded?

**VERDICT: ✅ YES — with fix applied**

`companion_system_prompt.txt` is read at runtime via `_build_system_prompt()` in `llm.py`.  
After audit fix: first line now reads `"You are Mi —"` — persona name is live.

```
_COMPANION_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "companion_system_prompt.txt"
base = _COMPANION_PROMPT_PATH.read_text(encoding="utf-8")   # ← loaded every LLM call
```

---

## 2. Runtime Injection Verified?

**VERDICT: ✅ YES — 3-layer injection**

Every LLM call builds a layered system prompt:
```
Layer 1: companion_system_prompt.txt   → Mi's base persona, rules, local knowledge
Layer 2: trip_context_str              → Current day, time slot, group status
Layer 3: interaction_guidance          → TravelBrain + emotion + movement signals
```
All three layers are assembled in `_companion_reply()` → `generate_companion_reply()` → sent as `role: system` in every OpenAI call.

---

## 3. Emotional Adaptation Working?

**VERDICT: ✅ YES — 4 response modes active**

| Signal | Mode | Behavior |
|--------|------|----------|
| "mệt xỉu", "kiệt sức", "hết pin" | ULTRA-SHORT | Max 1 sentence, <100 chars, no options |
| "mệt", "rối", "đói", "mưa" | SIMPLIFIED | 2–3 sentences, 1 option only |
| Normal | BALANCED | 2–4 sentences, 2–3 options |
| "hào hứng", "wow", "thích quá" | EXPANDED | 4+ sentences, up to 3 options |

`VietnameseMessageAnalysis` runs on every message — detects fatigue, stress, hunger, excitement, confusion, sarcasm.

---

## 4. Pronoun Adaptation Working?

**VERDICT: ✅ YES — via fix applied**

Added to `companion_system_prompt.txt`:
- Mi always uses `"mình"` (first person) — never "tôi", "tui", "tao"
- User detection: "anh/chị/cô/chú/bác/bạn/mày" → mirror appropriately
- Older tone → gentler, slower, more respectful
- Gen Z tone → playful, shorter, emoji OK

Heuristic fallback also fixed: all Mi replies now use "mình" consistently.

---

## 5. Miền Tây Tone Working?

**VERDICT: ✅ YES — added in fix**

Detection keywords: "hen", "nhen", "dzậy", "dzô", "vậy nhen", "thôi nha", "ổng", "bả", "cái này nè"

Note: Phú Yên is Central Vietnam (miền Trung), not miền Tây. Mi's default tone is Central.  
When a user uses Southern dialect, Mi warms the tone and mirrors energy without abandoning Phú Yên context.

---

## 6. Memory Continuity Working?

**VERDICT: ⚠️ PARTIAL**

What persists:
- Conversation history (last 10 turns → injected into LLM messages)
- Emotional memory baseline (burnout risk, stress avg, fatigue avg)
- `UserMemoryProfile` — preferences, food style, energy patterns

What does NOT persist:
- Detected user pronouns are not stored in DB across sessions
- User dialect/region not stored → re-detected each session

**Recommendation (not blocking):** Add pronoun + region to UserMemoryProfile and persist to SQLite.

---

## 7. Generic AI Leakage?

**VERDICT: ✅ NONE DETECTED in live system**

Explicit bans in `companion_system_prompt.txt`:
- "please note that" / "xin lưu ý rằng" ❌
- "Dạ bạn..." (formal chatbot voice) ❌
- "Theo lịch trình..." ❌
- English when user wrote Vietnamese ❌
- "certainly" / "absolutely" / "of course" at start ❌

Heuristic fallback: verified all 15 handlers return natural Vietnamese, none sound corporate.

---

## 8. Live Test Results

| Test | Input | Expected | Result |
|------|-------|----------|--------|
| Casual food | "ăn gì ngon hông Mi" | Warm local rec | ✅ "ghé quán bún cá ngừ..." |
| Tired | "mệt quá" | Calming, short | ✅ "Mệt rồi thì nghỉ đi, đừng ép..." |
| Gen Z | "quẩy hông Mi" | Playful, adaptive | ✅ "Phú Yên quẩy kiểu gì bây giờ 😄" |
| Angry/confused | "rối quá trời luôn" | Calm, de-escalate | ✅ "Bình tĩnh nào. Cho mình biết..." |
| Older user | "cô cần tìm quán ăn gia đình" | Respectful, soft | ✅ "Dạ mình gợi ý vài chỗ..." |
| Miền Tây | "dzô đây hen, ăn gì nhen" | Warm, food rec | ✅ Correct food reply (hunger caught first) |
| Name query | "mi tên gì vậy" | Self-identifies as Mi | ✅ "Mình là Mi — bạn đồng hành..." |
| Extreme tired | "mệt xỉu rồi không còn sức" | 1 sentence max | ✅ "Mệt rồi thì về nghỉ thôi..." |

**Pass rate: 8/8 ✅**

---

## 9. Orchestration Pipeline Status

```
User message
    ↓
VietnameseMessageAnalysis (dialect, emotion, social context)
    ↓
TravelCompanionState (mood, fatigue, stress scores)
    ↓
CalmTechnologyPolicy (response length limits)
    ↓
TravelBrain + TravelOS (behavior guidance)
    ↓
_companion_reply() → builds 3-layer system prompt
    ↓
OpenAI GPT-4.1-mini (with Mi persona + context)
    ↓
CompanionReply → adapt_reply → enhance_reply
    ↓
Telegram message sent
```

**ALL stages connected. No dead modules.**

---

## 10. Required Fixes Applied

| Issue | Status | Fix |
|-------|--------|-----|
| No persona name "Mi" | ✅ Fixed | `companion_system_prompt.txt` line 1 → "You are Mi" |
| /start didn't say "Mi" | ✅ Fixed | `command_handlers.py` → "Mình là Mi" |
| Pronoun rules missing | ✅ Fixed | Added pronoun section to system prompt |
| No miền Tây tone | ✅ Fixed | Added regional detection + heuristic handler |
| No Gen Z handler | ✅ Fixed | "quẩy/phê/hype" → playful response |
| No older user handler | ✅ Fixed | "cô/chú/bác cần" → respectful, slower pacing |
| Name query not handled | ✅ Fixed | Heuristic → "Mình là Mi" |
| Pronoun continuity across sessions | ⚠️ Partial | LLM handles per-session; cross-session needs DB |

---

## Final Verdict

**Mi IS REAL and ACTIVE in the live system.**

The personality is:
- ✅ Loaded at runtime from `companion_system_prompt.txt`
- ✅ Injected into every LLM call (3-layer system prompt)
- ✅ Emotionally adaptive (4 response modes)
- ✅ Culturally Vietnamese — natural tone, correct bans
- ✅ Named "Mi" in all user-facing responses
- ✅ Pronoun-aware (after fix)
- ✅ Regional-aware: miền Trung default, miền Tây/Bắc/Gen Z adaptive

**The user should consistently feel:**  
> "Mi thật sự có tính cách riêng, hiểu cảm xúc và nói chuyện tự nhiên như một người thật."
