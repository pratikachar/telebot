# Progress

## Project
Telegram multipurpose personal-assistant bot (Python). Goal: 100% free, no credit card required.

## Architecture map
- `main.py` — entry: registers all commands, callback handler, schedules digests + resumes reminders, polling.
- `handlers.py` — all handlers: basic, content, /ask chat, /reset, photo->study, settings, /email, /remind, /todo, desktop (/files /read /open /shot /install).
- `services.py` — API clients: Google News RSS, Open-Meteo, Yahoo (host fallback) + CoinGecko, TMDB, Google Books + Open Library fallback, iTunes, TheMealDB, deep-translator.
- `llm.py` — LLM cascade Gemini->Groq->Cerebras->GLM (OpenAI-compatible), text + vision (photos).
- `scheduler.py` — daily digest jobs (IST) + reminder jobs + resume on restart.
- `db.py` — SQLite: settings (city/lang/digest_time), chat history (last 10), reminders/todos.
- `email_service.py` — Gmail SMTP app-password email.
- `desktop.py` — list/read files, open apps, screenshot (Pillow), winget install (allowlist).
- `config.py` — .env loader + guards + owner/desktop gates.
- `requirements.txt` — PTB[job-queue] 22.8, feedparser, deep-translator, httpx, Pillow (all installed, all compile).

## Completed
- [x] ROADMAP.md: plan, no-card hosting truth (own hardware for 24/7), features, build phases.
- [x] Phase 1: skeleton + /start /help /menu /study + echo.
- [x] Phase 2: news/weather/stocks/movies/books/songs/recipe/translate — smoke-tested OK.
- [x] Phase 3: daily digest (/digest, /settime, /setcity, /setlang not wired) — verified output.
- [x] Phase 4: llm.py cascade + /ask + /reset + photo->study quiz. Verified: no-key returns friendly message; parser/desktop tests pass. NOTE: real LLM call not tested (no keys yet).
- [x] Phase 5: email_service + /email + /email digest + /remind (5m/2h/1d/HH:MM/tomorrow) + /todo (add/list/done/del) + reminder resume on restart.
- [x] Phase 6: desktop module gated by DESKTOP_CONTROL=1 + OWNER_ID; /files /read /open /shot /install(allowlist winget). Termux 24/7 deploy steps added to ROADMAP.
- [x] LLM upgrade: Gemini provider models updated to `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite` (+ 2.5 fallback). Cascade auto-skips unavailable models. llm.py + ROADMAP updated, compiles OK.
- [x] Groq fallback pool expanded: llama-3.3-70b, llama-3.1-8b, qwen/qwen3-32b, openai/gpt-oss-120b/20b, moonshotai/kimi-k2-instruct. All free-tier; auto-skipped on failure.
- [x] Robustness: `llm.chat()` wrapped so it NEVER raises — per-provider + per-model try/except, empty results ignored, config bugs contained. Returns (text, provider) or (None, None); handlers give friendly messages. Compiles OK.
- [x] Retry: `llm.chat()` now does up to 2 full cascade passes (`attempts=2`) per request for transient failures; still bounded (no infinite loop).
- [x] Gmail decision: user skips email for now — `/email` already returns a clean "not configured" message when GMAIL_* are blank (no code change needed).

## Next steps (ordered)
1. User pastes BOT_TOKEN in .env -> run `py main.py` -> test all commands from phone (PC on).
2. Add at least GEMINI_API_KEY (free) for /ask + study photos; optionally GROQ_API_KEY and ZAI_API_KEY for cascade fallback.
3. Optional: set OWNER_ID + DESKTOP_CONTROL=1 to use desktop control; add GMAIL_USER/APP_PASSWORD for /email; TMDB_API_KEY for /movies.
4. Verify real LLM cascade responses once a key is added.
5. Deploy 24/7: Termux on old phone (steps in ROADMAP section 8).

## Active bugs / errors
- None known. Yahoo Finance can transiently rate-limit (mitigated by query1/query2 fallback + pct-from-prev fix).
- Cerebras free tier now requires a payment method on file (documented; optional provider).
