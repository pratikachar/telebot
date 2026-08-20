# Progress

## Project
Telegram multipurpose personal-assistant bot (Python). Goal: 100% free, no credit card required.

## Architecture map
- `main.py` — entry: registers all commands, callback handler, schedules digests + resumes reminders, polling.
- `handlers.py` — all handlers: basic, content, /ask chat, /reset, photo->study, settings, /email, /remind, /todo, desktop (/files /read /open /shot /install), run/ui/code/skill/memory/voice.
- `services.py` — API clients: Google News RSS, Open-Meteo, Yahoo (host fallback) + CoinGecko, TMDB, Google Books + Open Library fallback, iTunes, TheMealDB, deep-translator, DuckDuckGo web search, Groq Whisper transcription.
- `llm.py` — LLM cascade Gemini->Groq->Cerebras->GLM (OpenAI-compatible), text + vision (photos).
- `scheduler.py` — daily digest jobs (IST) + reminder jobs + resume on restart.
- `db.py` — SQLite: settings (city/lang/digest_time/voice_reply), chat history (last 10), reminders/todos.
- `email_service.py` — Gmail SMTP app-password email.
- `desktop.py` — list/read files, open apps, screenshot (Pillow), winget install (allowlist), allowlisted /run, pyautogui UI actions, sandboxed /code.
- `memory.py` — long-term MEMORY.md read/append.
- `skills.py` — skills.json load/save/list/delete for /skill record+replay.
- `config.py` — .env loader + guards + owner/desktop gates.
- `requirements.txt` — PTB[job-queue] 22.8, feedparser, deep-translator, httpx, Pillow, pyautogui, edge-tts (all installed, all compile).

## Completed
- [x] ROADMAP.md: plan, no-card hosting truth (own hardware for 24/7), features, build phases.
- [x] Phase 1: skeleton + /start /help /menu /study + echo.
- [x] Phase 2: news/weather/stocks/movies/books/songs/recipe/translate — smoke-tested OK.
- [x] Phase 3: daily digest (/digest, /settime, /setcity) — verified output.
- [x] Phase 4: llm.py cascade + /ask + /reset + photo->study quiz. Verified with real keys (Gemini 3.6 Flash).
- [x] Phase 5: email_service + /email + /email digest + /remind + /todo + reminder resume on restart.
- [x] Phase 6: desktop module gated by DESKTOP_CONTROL=1 + OWNER_ID; /files /read /open /shot /install(allowlist winget).
- [x] LLM upgrade: Gemini provider models updated to `gemini-3.6-flash` -> `gemini-3.5-flash` -> `gemini-3.5-flash-lite` (+ 2.5 fallback). Cascade auto-skips unavailable models.
- [x] Groq fallback pool expanded: llama-3.3-70b, llama-3.1-8b, qwen/qwen3-32b, openai/gpt-oss-120b/20b, moonshotai/kimi-k2-instruct.
- [x] Robustness: `llm.chat()` NEVER raises — per-provider + per-model try/except, 2 full cascade passes (attempts=2), returns (text, provider) or (None, None).
- [x] Global owner lock: `owner_only()` decorator applied to ALL handlers (commands + echo + photo + voice + menu).
- [x] New `/summarize <path>`: reads local file (up to 2000 lines / 8k chars), summarizes via LLM.
- [x] Deps installed: python-telegram-bot 22.8, feedparser, deep-translator, apscheduler, pyautogui 0.9.54, edge-tts 7.2.8, beautifulsoup4.
- [x] File ops: `/create` `/append` `/delete` + `_resolve_path` (bare names -> Desktop), write verification, newline-aware append.
- [x] `/files -r` recursive listing (max 60); `/close` (taskkill), `/uninstall` (winget allowlist); tested live.
- [x] Command menu: `post_init` registers all commands via set_my_commands (now 45; verified 200 OK + getMyCommands).
- [x] **OpenClaw/Hermes-matching round (all implemented + tested):**
  - `/run <name>` — commands.txt allowlist (gitignored), subprocess no-shell, 60s timeout.
  - UI control: `/ui <instruction>` (screenshot -> Gemini vision -> JSON action), `/click x y`, `/type`, `/key`, `/scroll`, `/move` — every action STAGED, then `/confirm` or `/cancel`.
  - `/code <request>` — AI writes Python (extracts fenced/bare code), staged, `/confirm` runs sandboxed (temp dir, timeout 30s, stdout/stderr + PNGs returned).
  - `/skill learn <name>` + `/skill stop` (records confirmed UI steps to skills.json), `/skill <name>` replay, `/skill list|show|del`.
  - `/remember <fact>` — long-term MEMORY.md; `/ask` injects memory + live DuckDuckGo web results into context.
  - `/search <query>` — raw live web search results (DDG, no key, decoded real URLs).
  - Voice IN: voice notes -> Groq Whisper (whisper-large-v3-turbo, free) -> runs as command (via COMMAND_FUNCS) or /ask. Verified live transcription.
  - Voice OUT: `/voice on|off` — text always sent, plus TTS audio (edge-tts, free, en-IN-PrabhatNeural). Verified bytes generated.
  - Tests: py_compile all files OK; run_command (empty allowlist msg), code_exec (17 output + timeout), web_search (3 real results), memory/skills add/del, TTS 15.9KB, Whisper transcription, boot build 45 handlers + set_my_commands OK.

## Next steps (ordered)
1. User restarts bot (`Ctrl+C` then `py main.py`) to load all new handlers.
2. Add commands to `commands.txt` (format `name = command`) then test `/run <name>` from phone.
3. Test from phone: /ask (with web context), /search, /code 7+5*2 -> /confirm, /voice on then /ask, send a voice note, /remember + /ask.
4. Test UI actions carefully from phone: /click /type /key /scroll /move + /confirm (pyautogui moves the real mouse).
5. Optional: GMAIL_* for /email; TMDB_API_KEY for /movies.
6. Optional 24/7: Termux on old phone (steps in ROADMAP section 8).
7. Commit to git (`.env`, commands.txt, MEMORY.md, skills.json are gitignored).

## Active bugs / errors
- None known. Yahoo Finance can transiently rate-limit (mitigated by query1/query2 fallback + pct-from-prev fix).
- Cerebras free tier now requires a payment method on file (documented; optional provider).
- Windows subprocesses can't be fully network-isolated; /code sandbox = temp dir + timeout only (honest limit).
