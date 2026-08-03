# Telegram Multipurpose Bot — ROADMAP

A personal assistant Telegram bot built in Python. 100% free, **NO credit card required anywhere**.

---

## 1. What it will do

| Feature | Description | Free source |
|---|---|---|
| Morning digest | News + weather summary pushed daily at a fixed time | Google News RSS (no key), Open-Meteo (no key) |
| `/news` | Top headlines on demand | Google News RSS / NewsAPI free tier |
| `/weather <city>` | Current + forecast weather | Open-Meteo (no key needed) |
| `/movies` | New releases & what's showing | TMDB free tier (50 req/day) |
| `/books <query>` | Book search & recommendations | Google Books / Open Library (free) |
| `/songs <query>` | Song search & suggestions | iTunes Search API (free) |
| `/ask <question>` | General chat / Q&A | Gemini API free tier or Groq free tier |
| Email summary | "email me today's news" -> sends digest to your Gmail | Gmail SMTP + App Password (free) |
| Reminders & todos | Store tasks, get reminded at set times | SQLite (built-in) |
| Exam prep / study | Send a photo of a book page -> bot reads it and makes Q&A + quiz | Gemini free tier (multimodal, reads images) |
| AI chat /ask | General assistant chat, summaries, translation help | LLM cascade (see below) |
| Desktop control (owner) | /files /read /open /shot /install (winget) on the PC running the bot | Local, gated by .env |

---

## 2. Where it runs (NO credit card options)

The bot is a Python program that **polls** Telegram's API. It must be running to respond.

### Option A — Your own PC (simplest, zero cost)
- Run `py main.py`, bot works while your PC is on.
- Perfect for development and testing (Phase 1–5).

### Option B — Old Android phone via Termux (free, 24/7)
- Install **Termux**, install Python, run the bot 24/7 on a spare phone.
- Truly free, always on, no cloud, no card.

### Option C — Raspberry Pi / old laptop at home
- Same as B but on dedicated hardware. Free if you own one.

### Option D — PythonAnywhere web app (free cloud, no card) — PARTIAL, advanced
- Free = **1 web app** (request-driven) that wakes up when a request comes in.
- Can serve a **webhook** bot: Telegram pushes each message to your app's URL -> it responds. Works for on-demand commands.
- Free web apps expire after 1 month unless you log in/click a keep-alive link.
- NOT good for the morning push: free accounts have **no always-on tasks** (paid only) and no scheduled tasks for new signups. Workaround: use a free external cron (e.g. GitHub Actions) that calls a `/digest` endpoint on your app to send the morning message.

### Option E — Cloudflare Workers (free, no card)
- 100k requests/day free, no card.
- Serverless — requires **webhook** model and the bot written in JavaScript (not Python).
- Good later if you outgrow Python hosting; advanced.

### Hosting to AVOID in 2026 (they require a card or are now paid)
- **Hugging Face Spaces** — compute Spaces (Gradio/Docker = Python) now need a paid PRO plan; only static HTML/JS pages are free. NOT usable for a Python bot.
- Railway, Render, Fly.io, Oracle Cloud, Google Cloud — most free tiers now ask for card verification. Skip them.
- PythonAnywhere **always-on tasks** are paid-only, so it cannot run a 24/7 polling bot on free either.

**Recommendation:** Build locally first (Option A). For true free 24/7 without any card, the ONLY reliable way is Option B/C (your own hardware). If you want free cloud, use Option D (webhook) or E (JS/Workers) — both need extra workarounds for scheduled pushes.

**24/7 practical choice (confirmed):** old Android phone + Termux (`termux-wake-lock`) or an old laptop at home. Lightweight bot — even an old phone is fine. Needs only Wi-Fi + charger.

---

## 3. Telegram setup (2 minutes, no cost)
1. Open Telegram → search **@BotFather**
2. `/newbot` → pick a name and username → get a **token** like `123456:ABC-DEF...`
3. Store the token in a `.env` file (never share it, never commit it)
4. That's all — Telegram's API is free and unlimited.

---

## 4. Free APIs — what needs no card

| Service | Free | Card needed? |
|---|---|---|
| Google News RSS | Unlimited | No |
| Open-Meteo (weather) | Unlimited, no key | No |
| TMDB (movies) | 50 req/day | No |
| Google Books / Open Library | Unlimited | No |
| iTunes Search (songs) | Unlimited | No |
| Gemini API (chat/LLM) | ~15-30 req/min | No (Google account only) |
| Groq (chat/LLM) | Free tier | No |
| Gmail SMTP (email) | Free, needs App Password | No (Google account) |
| CoinGecko (crypto) | Unlimited | No |
| Frankfurter/ExchangeRate (FX) | Unlimited | No |
| free dictionaryapi.dev | Unlimited | No |
| DuckDuckGo Search | Unlimited | No |
| Wikipedia | Unlimited | No |

All accounts are just signups with an email — **no credit card anywhere**.

---

## 5. Build plan (6 phases)
> Hosting reality check (2026): no free cloud lets you run a 24/7 always-on Python polling bot without a card. Best real option = your own hardware (PC/phone/Pi).

### Phase 1 — Project skeleton + basic bot
- `main.py`, `config.py` (loads `.env`), `requirements.txt`
- `/start`, `/help`, echo reply
- Run locally, test in Telegram

### Phase 2 — Commands
- `/news`, `/weather <city>`, `/movies`, `/books`, `/songs`
- Clean keyboard buttons (`/start` menu) instead of typing commands

### Phase 3 — Morning scheduler
- `APScheduler`: 7:00 AM daily news + weather digest pushed to you
- Make time configurable via `/settime HH:MM` (your timezone)

### Phase 4 — Chat assistant
- `/ask <question>` via Gemini/Groq free tier
- Save chat history in SQLite so the bot remembers context

### Phase 5 — Email & tasks
- `/email` — Gmail SMTP sends summary to your inbox
- `/todo` + `/remind` — reminders stored in SQLite, fired by scheduler

### Phase 6 — Deploy 24/7
- Move to Termux / Raspberry Pi / Hugging Face Spaces
- Add logging, graceful restart, error notifications

---

## 6. Extra features to make it user-friendly & robust

**Ease of use**
- Inline keyboards / buttons for every command (no typing)
- `/menu` — pretty navigation menu with buttons (News, Weather, Stocks, Study, Translate, Remind...)
- `/help` — list of all capabilities
- Natural-language commands: "weather in Mumbai" instead of `/weather Mumbai`
- Per-user preferences stored in SQLite (`/settings` for city, time, timezone)
- Markdown/HTML formatting for clean output

**Content**
- Daily motivation quote, fun fact, or "on this day in history"
- Crypto prices, currency converter, stock quotes (yfinance)
- Sports scores / cricket live scores
- Dictionary & Wikipedia lookups, translations
- Voice notes → transcribe & reply (Whisper, local/free)
- RSS feeds you subscribe to (`/subscribe <feed>`)
- Image gen via Gemini free tier
- Weekly digest (summary of your week)

**Robustness**
- Logging to a file + errors auto-emailed/forwarded to you
- Retry with backoff for API failures; graceful shutdown
- Rate limiting (avoid Telegram spam bans)
- SQLite backups
- Handle 429 errors and token rotation
- Support multiple users (each with own preferences)
- Config via `.env`, nothing hard-coded

**Cost of everything above: $0.**

---

## 7. LLM cascade (AI chat + study photos) — all free tiers

Order: **Gemini -> Groq -> Cerebras -> GLM**. Any provider without a key is skipped; if one fails (rate limit/error), the next is tried automatically.

| Provider | Key in .env | Free models (2026) | Notes |
|---|---|---|---|
| Gemini | `GEMINI_API_KEY` (aistudio.google.com, no card) | `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite`, `gemini-2.5-flash` | Multimodal -> reads photos for exam prep; best default |
| Groq | `GROQ_API_KEY` (console.groq.com, no card) | `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, vision: `llama-4-scout` | Fastest, 30 RPM |
| Cerebras | `CEREBRAS_API_KEY` (cloud.cerebras.ai) | `gpt-oss-120b`, `gemma-4-31b` | NOTE: new free accounts need a payment method on file - optional |
| GLM (Z.ai) | `ZAI_API_KEY` (z.ai, no card) | `glm-4.7-flash`, `glm-4.5-flash`, vision: `glm-4.6v-flash` | Free, ~200K ctx, ~1 req/sec |

Add just one key to enable /ask; add all four for the most resilience.

---

## 8. Deploy 24/7 on an old Android phone (Termux)

1. Install **Termux** (F-Droid), then:
   ```
   pkg update && pkg install python -y
   pip install python-telegram-bot[job-queue] python-dotenv feedparser deep-translator httpx Pillow
   ```
2. Copy the `telebot` folder to the phone (USB / shared drive / `termux-setup-storage`).
3. Run once so the DB is created, then keep it alive:
   ```
   termux-wake-lock
   py main.py &
   ```
4. Keep the phone charged and on Wi-Fi. It now runs 24/7 for free.
5. Desktop-control commands only work when the bot runs on your PC (they act on that machine).
