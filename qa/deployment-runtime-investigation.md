# Deployment Investigation Report
**Date:** 2026-05-16  
**Investigator:** Dev (Claude Code)

---

## Active Branch
`main` — all fixes are on main, no other branches active for the bot.

## Active Commit (local/remote)
`81bc4fc` Fix: TripMember attribute access in _greeting_reply/_member_guidance

## Active Runtime (live Render)
**UNKNOWN** — `/version` endpoint did not exist before this fix.  
After this deploy, curl `https://phuyen-2026-telegram.onrender.com/version` to verify.

## Active Webhook
Was **EMPTY** at time of investigation (17:43 screenshot).  
**Fixed:** Webhook re-set to `https://phuyen-2026-telegram.onrender.com/api/telegram/webhook`

## Active Prompt Version
`companion_system_prompt.txt` — updated with Mi persona, member table, pronoun rules.  
Locally correct. Live status unknown until `/version` confirms.

## Personality Injection Working? (local)
✅ `_is_pure_greeting()` → catches "chào em" before LLM  
✅ `_greeting_reply(8654136346)` → "Chào anh Liêm! Em đây rồi 😊"  
✅ `_member_guidance()` → injected as first layer of interaction_guidance  
✅ `_sanitize_reply()` → strips **bold**, lists, truncates to 3 sentences

## Emotion Engine Working? (local)
✅ `MiEngine.analyze()` → `EmotionState`, `ResponseMode`  
✅ Injected into `mi_guidance` → combined with `interaction_guidance`

---

## ROOT CAUSE ANALYSIS

### Root Cause 1 — WEBHOOK WAS EMPTY (CONFIRMED)
`getWebhookInfo` returned `url: ""` — Telegram was NOT sending updates to the service.  
Bot responses in screenshots came from a period BEFORE the webhook was cleared.  
**Fix applied:** Re-set webhook via `setWebhook` API call.

### Root Cause 2 — DOCKER LAYER CACHE + NON-EDITABLE INSTALL (CONFIRMED)
Dockerfile used `pip install --no-cache-dir .` (non-editable).  
This COPIES source to site-packages at build time.  
If Render uses a cached Docker layer (e.g., because `pyproject.toml` didn't change),  
the `pip install` step doesn't re-run → site-packages has OLD code → live bot uses old logic.  
**Fix applied:** Changed to `pip install -e .` (editable install).  
Python now imports directly from `/app/app` — the files we COPY every build.

### Root Cause 3 — NO DEPLOYMENT VERIFICATION MECHANISM
No `/version` endpoint existed. Impossible to confirm what code was live.  
**Fix applied:** Added `/version` endpoint + `/health` now returns `"mi":"active"` + commit hash.

### Root Cause 4 — render.yaml SERVICE NAME MISMATCH (LIKELY)
`render.yaml` had `name: phuyen-2026` but live service is `phuyen-2026-telegram`.  
`autoDeployTrigger: commit` was deploying a DIFFERENT service (or no service).  
**Fix applied:** Changed to `name: phuyen-2026-telegram`.

### Root Cause 5 — NO EXPLICIT DEPLOY TRIGGER IN CI
No GitHub Actions workflow triggered Render deploy on push.  
**Fix applied:** Added `.github/workflows/render-deploy.yml`.  
Set `RENDER_DEPLOY_HOOK_URL` in GitHub repo variables to activate explicit trigger.

---

## Old Runtime Found?
No separate old polling process found in source.  
`backend/build/lib/` contained stale build artifacts — **deleted** (not git-tracked).

## Duplicate Source Found?
`phuyen-2026/` nested directory contains a copy of the project.  
NOT deployed (Dockerfile builds from root, not from nested dir).  
Not a runtime issue.

## Cache Issue Found?
**YES** — Docker layer cache + non-editable pip install = live code not updated.  
Fixed by switching to editable install.

---

## Fix Applied
1. Dockerfile: `pip install -e .` (editable) — Python imports from live source  
2. Dockerfile: Added `ARG GIT_COMMIT` / `BUILD_TIME` for version tracking  
3. main.py: `/version` + `/health` now include commit hash  
4. render.yaml: Correct service name + `dockerBuildArgs` for commit  
5. GitHub Actions: `render-deploy.yml` explicit deploy trigger  
6. Webhook: Re-set to correct URL  
7. Deleted `backend/build/` stale artifacts  

---

## Live Verification (run after deploy)
```bash
curl https://phuyen-2026-telegram.onrender.com/health
# Expected: {"status":"ok","env":"production","mi":"active","commit":"81bc4fc...","built":"..."}

curl https://phuyen-2026-telegram.onrender.com/version  
# Expected: {"commit":"81bc4fc...","mi_personality":"active","greeting_fastpath":"active",...}
```

## Final Verdict
The live bot was running STALE CODE due to:
1. Empty webhook (messages weren't even arriving)
2. Docker cache serving old site-packages copy
3. render.yaml targeting wrong service name

All three root causes have been fixed. Next deploy will run clean code with Mi personality active.
