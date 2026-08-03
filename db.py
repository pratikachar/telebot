import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.db")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS settings ("
            "chat_id INTEGER PRIMARY KEY,"
            "city TEXT DEFAULT 'Mumbai',"
            "lang TEXT DEFAULT 'en',"
            "digest_time TEXT DEFAULT '07:00')"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS history ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "chat_id INTEGER,"
            "role TEXT,"
            "content TEXT)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS reminders ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "chat_id INTEGER,"
            "text TEXT,"
            "remind_at TEXT,"
            "done INTEGER DEFAULT 0)"
        )


# ---- settings ----


def upsert(chat_id):
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO settings (chat_id, city, lang, digest_time) "
            "VALUES (?, 'Mumbai', 'en', '07:00')",
            (chat_id,),
        )


def get(chat_id):
    with _conn() as c:
        row = c.execute("SELECT * FROM settings WHERE chat_id = ?", (chat_id,)).fetchone()
        return dict(row) if row else None


def set_city(chat_id, city):
    with _conn() as c:
        c.execute("UPDATE settings SET city = ? WHERE chat_id = ?", (city, chat_id))


def set_lang(chat_id, lang):
    with _conn() as c:
        c.execute("UPDATE settings SET lang = ? WHERE chat_id = ?", (lang, chat_id))


def set_digest_time(chat_id, digest_time):
    with _conn() as c:
        c.execute("UPDATE settings SET digest_time = ? WHERE chat_id = ?", (digest_time, chat_id))


def all_chats():
    with _conn() as c:
        rows = c.execute("SELECT * FROM settings").fetchall()
        return [dict(r) for r in rows]


# ---- chat history ----


def add_history(chat_id, role, content):
    with _conn() as c:
        c.execute(
            "INSERT INTO history (chat_id, role, content) VALUES (?, ?, ?)",
            (chat_id, role, content),
        )
        c.execute("DELETE FROM history WHERE id NOT IN (SELECT id FROM history WHERE chat_id = ? ORDER BY id DESC LIMIT 10)", (chat_id,))


def get_history(chat_id):
    with _conn() as c:
        rows = c.execute(
            "SELECT role, content FROM history WHERE chat_id = ? ORDER BY id ASC", (chat_id,)
        ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]


def clear_history(chat_id):
    with _conn() as c:
        c.execute("DELETE FROM history WHERE chat_id = ?", (chat_id,))


# ---- reminders ----


def add_reminder(chat_id, text, remind_at):
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO reminders (chat_id, text, remind_at) VALUES (?, ?, ?)",
            (chat_id, text, remind_at),
        )
        return cur.lastrowid


def list_reminders(chat_id):
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM reminders WHERE chat_id = ? AND done = 0 ORDER BY remind_at ASC",
            (chat_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def mark_done(reminder_id):
    with _conn() as c:
        c.execute("UPDATE reminders SET done = 1 WHERE id = ?", (reminder_id,))


def delete_reminder(reminder_id):
    with _conn() as c:
        c.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))


def pending_future_reminders():
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM reminders WHERE done = 0 AND remind_at > ? ORDER BY remind_at ASC",
            (datetime_now_iso(),),
        ).fetchall()
        return [dict(r) for r in rows]


def datetime_now_iso():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    return datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()
