import datetime
from zoneinfo import ZoneInfo

import db
import services

TZ = ZoneInfo("Asia/Kolkata")


def _job_name(chat_id):
    return f"digest_{chat_id}"


async def build_digest(city, lang):
    parts = [f"\U000026A1 Good morning! Here's your digest ({city}):\n"]
    try:
        items = await services.get_news(None, lang)
        if isinstance(items, list):
            parts.append("\U0001F4F0 Top headlines:")
            for title, link in items[:5]:
                parts.append(f"\U00002022 {title}")
        else:
            parts.append("\U0001F4F0 News: unavailable")
    except Exception:
        parts.append("\U0001F4F0 News: unavailable")
    try:
        parts.append("")
        parts.append(await services.get_weather(city))
    except Exception:
        parts.append("")
        parts.append("\U0001F324 Weather: unavailable")
    try:
        parts.append("")
        parts.append("\U0001F4C8 Markets:")
        parts.append(await services.get_stocks())
    except Exception:
        parts.append("")
        parts.append("\U0001F4C8 Markets: unavailable")
    return "\n".join(parts)


def _add_job(job_queue, chat_id, digest_time, city, lang):
    hh, mm = (int(x) for x in digest_time.split(":"))
    job_queue.run_daily(
        send_digest,
        time=datetime.time(hour=hh, minute=mm),
        days=(0, 1, 2, 3, 4, 5, 6),
        name=_job_name(chat_id),
        tzinfo=TZ,
        data={"chat_id": chat_id, "city": city, "lang": lang},
    )


async def send_digest(context):
    job = context.job
    chat_id = job.data["chat_id"]
    city = job.data["city"]
    lang = job.data["lang"]
    try:
        text = await build_digest(city, lang)
        await context.bot.send_message(chat_id=chat_id, text=text)
    except Exception as exc:
        try:
            await context.bot.send_message(chat_id=chat_id, text=f"Digest failed: {exc}")
        except Exception:
            pass


def schedule_all(job_queue):
    if job_queue is None:
        return
    for row in db.all_chats():
        _add_job(job_queue, row["chat_id"], row["digest_time"], row["city"], row["lang"])


def reschedule_for(job_queue, chat_id):
    if job_queue is None:
        return
    for job in job_queue.get_jobs_by_name(_job_name(chat_id)):
        job.schedule_removal()
    row = db.get(chat_id)
    if row:
        _add_job(job_queue, row["chat_id"], row["digest_time"], row["city"], row["lang"])


# ---- reminders ----


def _reminder_name(reminder_id):
    return f"remind_{reminder_id}"


def schedule_reminder(job_queue, chat_id, text, when_dt):
    reminder_id = db.add_reminder(chat_id, text, when_dt.isoformat())
    job_queue.run_once(
        send_reminder,
        when=when_dt,
        name=_reminder_name(reminder_id),
        data={"chat_id": chat_id, "text": text},
    )
    return reminder_id


async def send_reminder(context):
    job = context.job
    try:
        await context.bot.send_message(
            chat_id=job.data["chat_id"],
            text=f"\U000023F0 Reminder:\n{job.data['text']}",
        )
    except Exception:
        pass
    try:
        db.mark_done(int(job.name.split("_")[1]))
    except Exception:
        pass


def resume_reminders(job_queue):
    if job_queue is None:
        return
    from datetime import datetime

    for row in db.pending_future_reminders():
        when = datetime.fromisoformat(row["remind_at"])
        if when.tzinfo is None:
            from zoneinfo import ZoneInfo

            when = when.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
        if when <= datetime.now(when.tzinfo):
            continue
        if not job_queue.get_jobs_by_name(_reminder_name(row["id"])):
            job_queue.run_once(
                send_reminder,
                when=when,
                name=_reminder_name(row["id"]),
                data={"chat_id": row["chat_id"], "text": row["text"]},
            )
