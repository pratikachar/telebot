import datetime
import json
import os
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from zoneinfo import ZoneInfo

import config
import db
import desktop
import email_service
import llm
from memory import memory_add, memory_read
import services
import skills as skills_db

TZ = ZoneInfo("Asia/Kolkata")


def owner_only(fn):
    async def wrapper(update, context):
        if not config.is_owner(update.effective_chat.id):
            if update.message:
                await update.message.reply_text("\U0001F6AB This bot is private.")
            return
        return await fn(update, context)

    return wrapper


def _resolve_path(path):
    """Bare filenames (no drive/folder) are resolved to the user's Desktop."""
    path = path.strip()
    if not os.path.isabs(path) and "\\" not in path and "/" not in path:
        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        return os.path.join(desktop_dir, path)
    return path

WELCOME = (
    "Hello! I'm your personal assistant bot. \U0001F916\n\n"
    "I can help you with:\n"
    "\U0001F4F0 News (politics / sports / tech / regional)\n"
    "\U0001F324 Weather\n"
    "\U0001F4C8 Stocks, Sensex, Nifty & crypto\n"
    "\U0001F3AC Movies, books & songs\n"
    "\U0001F35D Food / recipes\n"
    "\U0001F4DA Exam prep: send a photo of a book page for Q&A + quiz\n"
    "\U0001F4AC Chat with me: /ask anything\n"
    "\U00002709 Email summaries & reminders\n"
    "\U0001F5A5 Desktop control (owner only)\n\n"
    "Type /menu to see buttons, or /help for the full list."
)

HELP = (
    "Available commands:\n"
    "/start - welcome\n"
    "/menu - buttons menu\n"
    "/ask <question> - chat with AI (uses Gemini/Groq/GLM free tiers)\n"
    "/reset - clear chat memory\n"
    "/news [category] - headlines (politics, sports, tech, india, world...)\n"
    "/news [language] - news in hi/ta/te/bn/mr\n"
    "/weather <city> - weather forecast\n"
    "/stocks - Sensex, Nifty, crypto\n"
    "/movies - now showing in India\n"
    "/books <query> - book search\n"
    "/songs <query> - song suggestions\n"
    "/recipe <ingredients> - recipe ideas\n"
    "/translate <text> or /translate <lang>: <text>\n"
    "/email <text> - email a message to yourself\n"
    "/email digest - email today's digest\n"
    "/remind <when> <text> - e.g. /remind 5m call mom, /remind 21:00 water\n"
    "/todo - list todos  |  /todo add <task>  |  /todo done <id>  |  /todo del <id>\n"
    "/setcity <city> - save your city\n"
    "/settime HH:MM - set morning digest time\n"
    "/digest - run the morning digest right now\n"
    "/study - how exam prep works\n\n"
    "Owner-only desktop (needs DESKTOP_CONTROL=1):\n"
    "/files [path] - list folder (max 60)  |  /files -r [path] - list recursively (max 60 files)\n"
    "/read <file>  |  /open <app>  |  /close <app>  |  /shot  |  /install <app>  |  /uninstall <app>\n"
    "/summarize <file> - summarize a local text file (owner + desktop only)\n"
    "/create <file> [text] - create a new text file (owner + desktop only)\n"
    "/append <file> <text> - add a line to a file (owner + desktop only)\n"
    "/delete <file> - delete a file (owner + desktop only)\n"
    "/run <name> - run a command from commands.txt (allowlist)\n"
    "/ui <instruction> - AI looks at screen and picks an action (needs Gemini vision)\n"
    "/click x y | /type <text> | /key <key> | /scroll <n> | /move x y - stage a PC action, then /confirm\n"
    "/code <request> - AI writes Python, then /confirm runs it sandboxed (temp, timeout, no network)\n"
    "/skill learn <name> - record UI steps | /skill stop - save | /skill <name> - run\n"
    "/remember <fact> - store in long-term memory\n"
    "/voice on|off - also speak replies aloud (TTS)\n"
    "/search <query> - live web search\n\n"
    "Voice notes: send a voice message - I'll transcribe it and treat it as a command or /ask."
    "\n\nThis bot is private - only the owner can use it."
)

STUDY = (
    "Exam prep mode \U0001F4DA\n\n"
    "Send me a clear photo of a page from your book, notes, or diagram.\n"
    "I will read it and create key points, Q&A, and a quiz you can play.\n\n"
    "Image reading uses the Gemini free tier (add GEMINI_API_KEY in .env)."
)

MENU_BUTTONS = [
    [InlineKeyboardButton("\U0001F4F0 News", callback_data="menu_news")],
    [InlineKeyboardButton("\U0001F324 Weather", callback_data="menu_weather")],
    [InlineKeyboardButton("\U0001F4C8 Stocks & Crypto", callback_data="menu_stocks")],
    [InlineKeyboardButton("\U0001F3AC Movies / Books / Songs", callback_data="menu_media")],
    [InlineKeyboardButton("\U0001F35D Recipes", callback_data="menu_recipe")],
    [InlineKeyboardButton("\U0001F4DA Study / Exam prep", callback_data="menu_study")],
    [InlineKeyboardButton("\U0001F4AC Chat / Ask", callback_data="menu_chat")],
    [InlineKeyboardButton("\U00002709 Email & Reminders", callback_data="menu_email")],
    [InlineKeyboardButton("\U000026A1 Morning Digest", callback_data="menu_digest")],
]

MENU_HINTS = {
    "menu_news": "News: try /news politics, /news tech, /news hindi",
    "menu_weather": "Weather: try /weather Mumbai",
    "menu_stocks": "Stocks: try /stocks",
    "menu_media": "Media: try /movies, /books harry potter, /songs ed sheeran",
    "menu_recipe": "Recipes: try /recipe paneer tomato",
    "menu_study": "Study: send a photo of a book page - I'll make Q&A + quiz",
    "menu_chat": "Chat: try /ask what is inflation? or /translate hi: good morning",
    "menu_email": "Email: /email <text> or /remind 5m task or /todo add task",
    "menu_digest": "Morning digest: /digest now, /settime 07:00 to set the time",
}

LANG_NAMES = {
    "hindi": "hi", "tamil": "ta", "telugu": "te", "bengali": "bn",
    "marathi": "mr", "gujarati": "gu", "kannada": "kn", "malayalam": "ml",
    "punjabi": "pa", "english": "en", "french": "fr", "spanish": "es",
    "german": "de", "japanese": "ja", "korean": "ko", "chinese": "zh-CN",
    "arabic": "ar", "russian": "ru",
}

CHAT_SYSTEM = (
    "You are a helpful personal assistant in a Telegram bot. "
    "Answer in the same language the user writes in. Be concise and clear."
)

STUDY_SYSTEM = (
    "You are an exam-prep tutor. Read the text in the image carefully. "
    "Then reply with:\n"
    "1. KEY POINTS - the 3-5 most important ideas\n"
    "2. Q&A - 5 questions with short answers\n"
    "3. QUIZ - a 3-question multiple choice quiz (with answers listed at the end)"
)


async def _reply(update, text):
    if not text:
        return
    for i in range(0, len(text), 3900):
        await update.message.reply_text(text[i : i + 3900])


def _parse_translate(args):
    full = " ".join(args).strip()
    m = re.match(r"^(?:to\s+)?([a-zA-Z]{2,15})\s*:\s*(.+)$", full, re.IGNORECASE)
    if m:
        lang_word = m.group(1).lower()
        return LANG_NAMES.get(lang_word, lang_word), m.group(2).strip()
    return "en", full


def _parse_remind_time(token):
    now = datetime.datetime.now(TZ)
    m = re.match(r"^(?:in\s+)?(\d+)\s*(m|min|minute|h|hr|hour|d|day)s?$", token, re.I)
    if m:
        n = int(m.group(1))
        u = m.group(2).lower()[0]
        delta = (
            datetime.timedelta(minutes=n)
            if u == "m"
            else datetime.timedelta(hours=n)
            if u == "h"
            else datetime.timedelta(days=n)
        )
        return now + delta
    m = re.match(r"^(\d{1,2}):(\d{2})$", token)
    if m:
        hh, mm = int(m.group(1)), int(m.group(2))
        dt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if dt <= now:
            dt += datetime.timedelta(days=1)
        return dt
    m = re.match(r"^tomorrow\s+(\d{1,2}):(\d{2})$", token, re.I)
    if m:
        hh, mm = int(m.group(1)), int(m.group(2))
        return (now + datetime.timedelta(days=1)).replace(
            hour=hh, minute=mm, second=0, microsecond=0
        )
    return None


def _desktop_ok(update) -> bool:
    if not config.DESKTOP_CONTROL:
        return False
    return config.is_owner(update.effective_chat.id)


# ---------- basic ----------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db.upsert(update.effective_chat.id)
    await update.message.reply_text(WELCOME)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Pick a feature:", reply_markup=InlineKeyboardMarkup(MENU_BUTTONS)
    )


async def menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(MENU_HINTS.get(query.data, "Coming soon."))


async def study_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(STUDY)


# ---------- content commands ----------


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Fetching news \U0001F50D...")
    settings = db.get(update.effective_chat.id) or {}
    lang = settings.get("lang", "en")
    args = context.args or []
    category = args[0] if args else None
    try:
        items = await services.get_news(category, lang)
        if isinstance(items, str):
            await _reply(update, items)
            return
        lines = [f"\U0001F4F0 {category or 'Top'} headlines:\n"]
        for title, link in items:
            lines.append(f"\U00002022 {title}\n  {link}")
        await _reply(update, "\n".join(lines))
    except Exception as exc:
        await update.message.reply_text(f"News failed: {exc}")


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = db.get(update.effective_chat.id) or {}
    city = " ".join(context.args) if context.args else settings.get("city", "Mumbai")
    await update.message.reply_text("Fetching weather \U0001F324...")
    try:
        await _reply(update, await services.get_weather(city))
    except Exception as exc:
        await update.message.reply_text(f"Weather failed: {exc}")


async def stocks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Fetching markets \U0001F4C8...")
    try:
        await _reply(update, await services.get_stocks())
    except Exception as exc:
        await update.message.reply_text(f"Stocks failed: {exc}")


async def movies_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Fetching movies \U0001F3AC...")
    try:
        await _reply(update, await services.get_movies())
    except Exception as exc:
        await update.message.reply_text(f"Movies failed: {exc}")


async def books_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(context.args).strip()
    if not query:
        await update.message.reply_text("Usage: /books <query> e.g. /books atomic habits")
        return
    await update.message.reply_text("Searching books \U0001F4DA...")
    try:
        await _reply(update, await services.get_books(query))
    except Exception as exc:
        await update.message.reply_text(f"Books failed: {exc}")


async def songs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(context.args).strip()
    if not query:
        await update.message.reply_text("Usage: /songs <query> e.g. /songs ed sheeran")
        return
    await update.message.reply_text("Searching songs \U0001F3B5...")
    try:
        await _reply(update, await services.get_songs(query))
    except Exception as exc:
        await update.message.reply_text(f"Songs failed: {exc}")


async def recipe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ingredients = " ".join(context.args).strip()
    if not ingredients:
        await update.message.reply_text("No ingredients given - here's a random recipe \U0001F35D")
    try:
        await _reply(update, await services.get_recipe(ingredients))
    except Exception as exc:
        await update.message.reply_text(f"Recipe failed: {exc}")


async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target, text = _parse_translate(context.args)
    if not text:
        await update.message.reply_text(
            "Usage: /translate <text>  or  /translate hi: good morning"
        )
        return
    try:
        result = services.translate(text, target)
        await update.message.reply_text(f"\U0001F310 {target}:\n{result}")
    except Exception as exc:
        await update.message.reply_text(f"Translation failed: {exc}")


# ---------- AI chat ----------


async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question = " ".join(context.args).strip() if context.args else ""
    if not question:
        await update.message.reply_text("Usage: /ask <your question> e.g. /ask what is inflation?")
        return
    chat_id = update.effective_chat.id
    await update.message.reply_text("Thinking \U0001F9E0...")
    system = CHAT_SYSTEM
    mem = memory_read()
    if mem:
        system += f"\n\nContext you remember about the user:\n{mem}"
    try:
        results = await services.web_search(question, num=4)
        if results:
            ctx = "\n".join(f"- {title}: {link} - {snippet}" for title, link, snippet in results)
            system += f"\n\nLive web results (use them if relevant):\n{ctx}"
    except Exception:
        pass
    messages = [{"role": "system", "content": system}]
    messages.extend(db.get_history(chat_id))
    messages.append({"role": "user", "content": question})
    try:
        answer, provider = await llm.chat(messages)
    except Exception as exc:
        await update.message.reply_text(f"Chat failed: {exc}")
        return
    if not answer:
        await update.message.reply_text(
            "No AI provider is configured. Add one free key in .env to chat: "
            "GEMINI_API_KEY (aistudio.google.com) or GROQ_API_KEY (console.groq.com)."
        )
        return
    db.add_history(chat_id, "user", question)
    db.add_history(chat_id, "assistant", answer)
    await _reply(update, answer)
    if db.get_voice_reply(chat_id):
        await _send_voice(update, answer)
    await update.message.reply_text(f"_via {provider}_")


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(context.args).strip()
    if not query:
        await update.message.reply_text("Usage: /search <query>")
        return
    await update.message.reply_text("Searching the web \U0001F50D...")
    try:
        results = await services.web_search(query, num=6)
        if not results:
            await update.message.reply_text("No results found.")
            return
        lines = [f"\U0001F50D Results for '{query}':\n"]
        for title, link, snippet in results:
            lines.append(f"\U00002022 {title}")
            lines.append(f"  {link}")
            if snippet:
                lines.append(f"  {snippet[:150]}")
        await _reply(update, "\n".join(lines))
    except Exception as exc:
        await update.message.reply_text(f"Search failed: {exc}")


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db.clear_history(update.effective_chat.id)
    await update.message.reply_text("Chat memory cleared.")


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Reading your page \U0001F50D (needs Gemini key)...")
    file = await update.message.photo[-1].get_file()
    image_bytes = await file.download_as_bytearray()
    messages = [{"role": "system", "content": STUDY_SYSTEM}, {"role": "user", "content": "Here is the page."}]
    try:
        answer, provider = await llm.chat(messages, image_bytes=bytes(image_bytes))
    except Exception as exc:
        await update.message.reply_text(f"Study failed: {exc}")
        return
    if not answer:
        await update.message.reply_text(
            "No vision-capable AI configured. Add GEMINI_API_KEY (free) in .env "
            "to read photos for exam prep."
        )
        return
    await _reply(update, answer)
    await update.message.reply_text(f"_via {provider}_")


# ---------- settings ----------


async def setcity_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    city = " ".join(context.args).strip()
    if not city:
        await update.message.reply_text("Usage: /setcity Mumbai")
        return
    db.upsert(update.effective_chat.id)
    db.set_city(update.effective_chat.id, city)
    await update.message.reply_text(f"City saved: {city}")


async def settime_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    t = context.args[0] if context.args else ""
    if not re.match(r"^\d{1,2}:\d{2}$", t):
        await update.message.reply_text("Usage: /settime 07:00 (24h format)")
        return
    db.upsert(update.effective_chat.id)
    db.set_digest_time(update.effective_chat.id, t)
    await update.message.reply_text(f"Morning digest time set to {t} (IST)")
    from scheduler import reschedule_for

    reschedule_for(context.job_queue, update.effective_chat.id)


async def digest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = db.get(update.effective_chat.id) or {}
    await update.message.reply_text("Building your digest \U000026A1...")
    try:
        from scheduler import build_digest

        text = await build_digest(settings.get("city", "Mumbai"), settings.get("lang", "en"))
        await _reply(update, text)
    except Exception as exc:
        await update.message.reply_text(f"Digest failed: {exc}")


# ---------- email ----------


async def email_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = " ".join(context.args).strip()
    if not args:
        await update.message.reply_text("Usage: /email <message>  or  /email digest")
        return
    await update.message.reply_text("Sending email \U00002709...")
    try:
        if args.lower() == "digest":
            settings = db.get(update.effective_chat.id) or {}
            from scheduler import build_digest

            body = await build_digest(settings.get("city", "Mumbai"), settings.get("lang", "en"))
            subject = f"Daily digest ({settings.get('city', 'Mumbai')})"
        else:
            body = args
            subject = "Message from your Telegram assistant"
        to = email_service.send_email(subject, body)
        await update.message.reply_text(f"Email sent to {to} \u2705")
    except Exception as exc:
        await update.message.reply_text(f"Email failed: {exc}")


# ---------- reminders & todos ----------


async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "Usage:\n/remind 5m call mom\n/remind 21:00 water plants\n/remind tomorrow 9:00 meeting"
        )
        return
    when = _parse_remind_time(context.args[0])
    if not when:
        await update.message.reply_text(
            "Couldn't understand the time. Use e.g. 5m, 2h, 1d, 21:00, tomorrow 9:00"
        )
        return
    text = " ".join(context.args[1:]).strip() or "Reminder"
    reminder_id = schedule_reminder_job(context, update.effective_chat.id, text, when)
    await update.message.reply_text(
        f"\U000023F0 Reminder #{reminder_id} set for {when.strftime('%d %b %H:%M')}:\n{text}"
    )


def schedule_reminder_job(context, chat_id, text, when_dt):
    from scheduler import schedule_reminder

    return schedule_reminder(context.job_queue, chat_id, text, when_dt)


async def todo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    args = context.args or []
    if not args:
        items = db.list_reminders(chat_id)
        if not items:
            await update.message.reply_text("No todos. Try /todo add buy milk")
            return
        lines = ["\U0001F4CB Your todos & reminders:\n"]
        for r in items:
            lines.append(f"#{r['id']} {r['text']}  ({r['remind_at'][:16].replace('T', ' ')})")
        await _reply(update, "\n".join(lines))
        return
    action = args[0].lower()
    rest = " ".join(args[1:]).strip()
    if action == "add":
        if not rest:
            await update.message.reply_text("Usage: /todo add <task>")
            return
        rid = db.add_reminder(chat_id, rest, datetime.datetime.now(TZ).isoformat())
        await update.message.reply_text(f"Added todo #{rid}")
    elif action in ("done", "del", "delete"):
        if not rest or not rest.isdigit():
            await update.message.reply_text(f"Usage: /todo {action} <id>")
            return
        if action == "done":
            db.mark_done(int(rest))
        else:
            db.delete_reminder(int(rest))
        await update.message.reply_text(f"Todo #{rest} updated.")
    else:
        await update.message.reply_text("Sub-commands: /todo add <task> | /todo done <id> | /todo del <id>")


# ---------- desktop control ----------


async def files_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    recursive = bool(context.args and context.args[0] == "-r")
    path = " ".join(context.args[1:] if recursive else context.args).strip()
    try:
        await _reply(update, desktop.list_dir(path, recursive=recursive))
    except Exception as exc:
        await update.message.reply_text(f"Error: {exc}")


async def read_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    path = _resolve_path(" ".join(context.args).strip())
    if not path:
        await update.message.reply_text("Usage: /read <file path>")
        return
    try:
        await _reply(update, desktop.read_file(path))
    except Exception as exc:
        await update.message.reply_text(f"Error: {exc}")


async def summarize_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    path = _resolve_path(" ".join(context.args).strip())
    if not path:
        await update.message.reply_text("Usage: /summarize <file path>")
        return
    try:
        text = desktop.read_file(path, max_lines=2000)
    except Exception as exc:
        await update.message.reply_text(f"Read failed: {exc}")
        return
    if len(text) > 8000:
        text = text[:8000]
    await update.message.reply_text("Summarizing \U0001F9E0...")
    messages = [
        {"role": "system", "content": "Summarize the following file content concisely in bullet points."},
        {"role": "user", "content": text},
    ]
    try:
        answer, provider = await llm.chat(messages)
    except Exception as exc:
        await update.message.reply_text(f"Summarize failed: {exc}")
        return
    if not answer:
        await update.message.reply_text(
            "No AI provider configured. Add a free key (GEMINI_API_KEY) in .env to summarize."
        )
        return
    await _reply(update, answer)
    await update.message.reply_text(f"_via {provider}_")


async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /create <file path> [text]")
        return
    path = _resolve_path(context.args[0])
    # Everything after the first argument is the file content (optional)
    text = " ".join(context.args[1:]) if len(context.args) > 1 else ""
    result = desktop.create_file(path, text)
    await update.message.reply_text(result)


async def append_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /append <file path> <text to add>")
        return
    path = _resolve_path(context.args[0])
    text = " ".join(context.args[1:])
    result = desktop.append_file(path, text)
    await update.message.reply_text(result)


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /delete <file path>")
        return
    path = _resolve_path(context.args[0])
    result = desktop.delete_file(path)
    await update.message.reply_text(result)


async def open_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    app = " ".join(context.args).strip()
    if not app:
        await update.message.reply_text("Usage: /open <app> (notepad, calc, chrome, explorer...)")
        return
    try:
        await update.message.reply_text(desktop.open_app(app))
    except Exception as exc:
        await update.message.reply_text(f"Error: {exc}")


async def close_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    app = " ".join(context.args).strip()
    if not app:
        await update.message.reply_text("Usage: /close <app> (notepad, calc, chrome, explorer...)")
        return
    try:
        await update.message.reply_text(desktop.close_app(app))
    except Exception as exc:
        await update.message.reply_text(f"Error: {exc}")


async def uninstall_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    app = " ".join(context.args).strip()
    if not app:
        await update.message.reply_text("Usage: /uninstall <app> (same allowlist as /install)")
        return
    await update.message.reply_text(f"Uninstalling {app} via winget... \U000023F3")
    try:
        await _reply(update, desktop.uninstall(app))
    except Exception as exc:
        await update.message.reply_text(f"Uninstall failed: {exc}")


async def shot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    try:
        buf = desktop.screenshot()
        await update.message.reply_photo(photo=buf, caption="Screenshot \U0001F4F7")
    except Exception as exc:
        await update.message.reply_text(f"Screenshot failed: {exc}")


async def install_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    app = " ".join(context.args).strip()
    if not app:
        await update.message.reply_text("Usage: /install <app> e.g. /install nodejs")
        return
    await update.message.reply_text(f"Installing {app} via winget... \U000023F3")
    try:
        await _reply(update, desktop.install(app))
    except Exception as exc:
        await update.message.reply_text(f"Install failed: {exc}")


# ---------- run / ui / code / skill / memory / voice ----------


async def _send_voice(update, text):
    """Send a spoken (TTS) version of the answer alongside text. Best effort, never fails."""
    try:
        import edge_tts
        import io as _io

        text = text[:900]
        com = edge_tts.Communicate(text, "en-IN-PrabhatNeural")
        buf = _io.BytesIO()
        async for chunk in com.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        if buf.getbuffer().nbytes == 0:
            return
        buf.seek(0)
        await update.message.reply_audio(audio=buf, title="Spoken reply")
    except Exception:
        pass


async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not config.is_owner(update.effective_chat.id):
        await update.message.reply_text("\U0001F6AB This bot is private.")
        return
    await update.message.reply_text("Listening \U0001F3A4...")
    file = await update.message.voice.get_file()
    audio_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp", f"voice_{update.message.message_id}.ogg")
    await file.download_to_drive(audio_path)
    try:
        text = await services.transcribe_voice(audio_path)
    finally:
        try:
            os.remove(audio_path)
        except OSError:
            pass
    if not text:
        await update.message.reply_text("Could not hear anything. Please try again.")
        return
    await update.message.reply_text(f"You said: {text}")
    if text.startswith("/"):
        cmd = text.split()[0][1:].lower()
        args = text.split()[1:]
        target = COMMAND_FUNCS.get(cmd)
        if target:
            context.args = args
            await target(update, context)
            return
    context.args = text.split()
    await ask_command(update, context)


async def remember_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text("Usage: /remember <fact to remember>")
        return
    memory_add(text)
    await update.message.reply_text("Remembered \U0001F4DD")


async def voice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    arg = (context.args[0] if context.args else "").lower()
    db.upsert(update.effective_chat.id)
    if arg in ("on", "1", "yes"):
        db.set_voice_reply(update.effective_chat.id, True)
        await update.message.reply_text("Voice replies ON - I'll also speak my answers.")
    elif arg in ("off", "0", "no"):
        db.set_voice_reply(update.effective_chat.id, False)
        await update.message.reply_text("Voice replies OFF - text only.")
    else:
        state = "ON" if db.get_voice_reply(update.effective_chat.id) else "OFF"
        await update.message.reply_text(f"Voice replies are {state}. Usage: /voice on | /voice off")


async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    name = " ".join(context.args).strip()
    if not name:
        await update.message.reply_text("Usage: /run <command name> (defined in commands.txt)")
        return
    await update.message.reply_text(desktop.run_command(name))


def _apply_step(step):
    """Execute one UI step dict and return its result text."""
    a = step.get("action")
    if a == "click":
        return desktop.click(step["x"], step["y"], step.get("button", "left"))
    if a == "type":
        return desktop.type_text(step["text"])
    if a == "key":
        return desktop.key_press(step["key"])
    if a == "scroll":
        return desktop.scroll(step["clicks"])
    if a == "move":
        return desktop.move_mouse(step["x"], step["y"])
    if a == "open":
        return desktop.open_app(step["app"])
    if a == "run":
        return desktop.run_command(step["name"])
    return f"Unknown action: {a}"


async def _stage_ui(update, context, step, desc):
    context.user_data["pending"] = {"kind": "ui", "step": step}
    await update.message.reply_text(
        f"\U0001F4C1 Staged: {desc}\nReply /confirm to do it, /cancel to drop it."
    )


def _record_skill_step(context, step):
    """While a skill is being recorded, append the confirmed step."""
    recording = context.user_data.get("skill_recording")
    if recording:
        context.user_data.setdefault("skill_steps", []).append(step)


async def click_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /click x y  e.g. /click 500 300")
        return
    try:
        x, y = int(context.args[0]), int(context.args[1])
    except ValueError:
        await update.message.reply_text("Coordinates must be numbers.")
        return
    button = context.args[2] if len(context.args) > 2 else "left"
    await _stage_ui(update, context, {"action": "click", "x": x, "y": y, "button": button}, f"Click {button} at ({x}, {y})")


async def type_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: /type <text to type>")
        return
    await _stage_ui(update, context, {"action": "type", "text": text}, f"Type: {text[:60]}")


async def key_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    key = context.args[0].lower() if context.args else ""
    if not key:
        await update.message.reply_text("Usage: /key <key> e.g. /key enter, /key ctrl+alt+del")
        return
    await _stage_ui(update, context, {"action": "key", "key": key}, f"Press key: {key}")


async def scroll_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    try:
        clicks = int(context.args[0]) if context.args else 0
    except ValueError:
        await update.message.reply_text("Usage: /scroll <amount>  (negative = down)")
        return
    if clicks == 0:
        await update.message.reply_text("Usage: /scroll <amount> e.g. /scroll -3")
        return
    await _stage_ui(update, context, {"action": "scroll", "clicks": clicks}, f"Scroll {clicks}")


async def move_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    try:
        x, y = int(context.args[0]), int(context.args[1])
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /move x y")
        return
    await _stage_ui(update, context, {"action": "move", "x": x, "y": y}, f"Move mouse to ({x}, {y})")


async def ui_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    instruction = " ".join(context.args).strip()
    if not instruction:
        await update.message.reply_text("Usage: /ui <instruction> e.g. /ui click the search box")
        return
    await update.message.reply_text("Looking at the screen \U0001F50D...")
    try:
        img = desktop.screenshot().read()
    except Exception as exc:
        await update.message.reply_text(f"Screenshot failed: {exc}")
        return
    prompt = (
        "You control this Windows PC by looking at the screenshot. "
        f"Task: {instruction}\n"
        "Reply with ONLY a JSON object describing ONE action, no other text:\n"
        '{"action":"click","x":<int>,"y":<int>,"button":"left"}\n'
        '{"action":"type","text":"<text to type>"}\n'
        '{"action":"key","key":"<key like enter, tab, esc>"}\n'
        '{"action":"scroll","clicks":<int positive=up negative=down>}\n'
        '{"action":"move","x":<int>,"y":<int>}\n'
        '{"action":"open","app":"<app name>"}\n'
        '{"action":"run","name":"<command name from commands.txt>"}\n'
        'If unsure, reply {"action":"move","x":0,"y":0}.'
    )
    messages = [
        {"role": "system", "content": "You output only valid JSON."},
        {"role": "user", "content": prompt},
    ]
    try:
        answer, provider = await llm.chat(messages, image_bytes=img)
    except Exception as exc:
        await update.message.reply_text(f"Vision failed: {exc}")
        return
    if not answer:
        await update.message.reply_text("No vision-capable AI configured (needs GEMINI_API_KEY).")
        return
    step = _parse_ui_json(answer)
    if not step:
        await update.message.reply_text(f"Could not parse the AI action. Raw reply:\n{answer[:500]}")
        return
    desc = f"{step.get('action')} {json.dumps({k: v for k, v in step.items() if k != 'action'})}"
    await _stage_ui(update, context, step, f"{provider}: {desc}")


def _parse_ui_json(text):
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except Exception:
        return None
    if not isinstance(data, dict) or "action" not in data:
        return None
    return data


async def confirm_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pending = context.user_data.get("pending")
    if not pending:
        await update.message.reply_text("Nothing is staged. Use /click, /type, /ui, /code first.")
        return
    context.user_data["pending"] = None
    if pending["kind"] == "ui":
        try:
            result = _apply_step(pending["step"])
        except Exception as exc:
            await update.message.reply_text(f"Action failed: {exc}")
            return
        await update.message.reply_text(result)
        _record_skill_step(context, pending["step"])
    elif pending["kind"] == "code":
        await update.message.reply_text("Running code in a sandbox \U0001F9EA...")
        output, pngs = desktop.code_exec(pending["code"])
        await _reply(update, output)
        for p in pngs:
            try:
                with open(p, "rb") as f:
                    await update.message.reply_photo(photo=f, caption="Generated image")
            except Exception:
                pass


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["pending"] = None
    await update.message.reply_text("Staged action cancelled.")


async def code_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    request = " ".join(context.args).strip()
    if not request:
        await update.message.reply_text(
            "Usage: /code <python request> e.g. /code 7+5*2 or /code make a plot of x^2"
        )
        return
    await update.message.reply_text("Writing code \U0001F4DD...")
    prompt = (
        "Write Python code to do the following. Return ONLY the code inside ```python fences, "
        f"no explanation.\nTask: {request}"
    )
    messages = [
        {"role": "system", "content": "You write only Python code, no explanations."},
        {"role": "user", "content": prompt},
    ]
    try:
        answer, provider = await llm.chat(messages)
    except Exception as exc:
        await update.message.reply_text(f"Code gen failed: {exc}")
        return
    if not answer:
        await update.message.reply_text("No AI provider configured (needs a free key in .env).")
        return
    code = _extract_python(answer)
    if not code:
        await update.message.reply_text(f"No code found in reply:\n{answer[:500]}")
        return
    preview = code[:1200]
    context.user_data["pending"] = {"kind": "code", "code": code}
    await update.message.reply_text(
        f"{provider} wrote this code:\n\n{preview}\n\nReply /confirm to run it in the sandbox, /cancel to drop it."
    )


def _extract_python(text):
    m = re.search(r"```(?:python)?\s*(.*?)```", text, re.S)
    if m:
        return m.group(1).strip()
    lines = [l for l in text.strip().splitlines() if not l.startswith("```")]
    candidate = "\n".join(lines).strip()
    if candidate:
        return candidate
    return None


async def skill_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _desktop_ok(update):
        await update.message.reply_text("Desktop control is disabled or you're not the owner.")
        return
    args = context.args or []
    action = args[0].lower() if args else ""
    name = args[1] if len(args) > 1 else ""
    if action == "list":
        names = skills_db.skill_list()
        await update.message.reply_text("Skills: " + (", ".join(names) if names else "none"))
        return
    if action == "del" and name:
        if skills_db.skill_delete(name):
            await update.message.reply_text(f"Deleted skill: {name}")
        else:
            await update.message.reply_text(f"Skill not found: {name}")
        return
    if action == "learn":
        if not name:
            await update.message.reply_text("Usage: /skill learn <name>  then confirm actions, then /skill stop")
            return
        context.user_data["skill_recording"] = name
        context.user_data["skill_steps"] = []
        await update.message.reply_text(
            f"Recording skill '{name}'. Now /click /type /key /scroll /move /run and confirm each. "
            "Send /skill stop when done."
        )
        return
    if action == "stop":
        steps = context.user_data.pop("skill_steps", [])
        name = context.user_data.pop("skill_recording", name or "unnamed")
        if not steps:
            await update.message.reply_text("Nothing recorded. Cancelled.")
            return
        skills_db.skill_add(name, steps)
        await update.message.reply_text(f"Skill '{name}' saved with {len(steps)} steps.")
        return
    if action == "show" and name:
        skill = skills_db.skill_get(name)
        if not skill:
            await update.message.reply_text(f"Skill not found: {name}")
            return
        lines = [f"\U0001F4CB Skill '{name}':"]
        for i, s in enumerate(skill["steps"], 1):
            lines.append(f"{i}. {s.get('action')} {json.dumps({k: v for k, v in s.items() if k != 'action'})}")
        await _reply(update, "\n".join(lines))
        return
    if action and action not in ("list", "del", "learn", "stop", "show"):
        name = action
        skill = skills_db.skill_get(name)
        if not skill:
            await update.message.reply_text(f"Skill not found: {name}")
            return
        results = []
        for s in skill["steps"]:
            try:
                results.append(_apply_step(s))
            except Exception as exc:
                results.append(f"Step {s.get('action')} failed: {exc}")
        await _reply(update, "\n".join(results))
        return
    await update.message.reply_text(
        "Usage:\n/skill learn <name>  - record steps\n/skill stop - save recording\n"
        "/skill <name> - run a skill\n/skill list\n/skill show <name>\n/skill del <name>"
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"You said: {update.message.text}\n\nUse /menu or /help to see what I can do."
    )


COMMAND_FUNCS = {
    "start": start,
    "help": help_command,
    "menu": menu_command,
    "study": study_command,
    "news": news_command,
    "weather": weather_command,
    "stocks": stocks_command,
    "movies": movies_command,
    "books": books_command,
    "songs": songs_command,
    "recipe": recipe_command,
    "translate": translate_command,
    "ask": ask_command,
    "search": search_command,
    "reset": reset_command,
    "email": email_command,
    "remind": remind_command,
    "todo": todo_command,
    "setcity": setcity_command,
    "settime": settime_command,
    "digest": digest_command,
    "files": files_command,
    "read": read_command,
    "summarize": summarize_command,
    "create": create_command,
    "append": append_command,
    "delete": delete_command,
    "open": open_command,
    "close": close_command,
    "shot": shot_command,
    "install": install_command,
    "uninstall": uninstall_command,
    "run": run_command,
    "ui": ui_command,
    "click": click_command,
    "type": type_command,
    "key": key_command,
    "scroll": scroll_command,
    "move": move_command,
    "confirm": confirm_command,
    "cancel": cancel_command,
    "code": code_command,
    "skill": skill_command,
    "remember": remember_command,
    "voice": voice_command,
}
