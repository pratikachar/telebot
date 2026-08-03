import logging

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

import db
import handlers
from config import BOT_TOKEN
from scheduler import resume_reminders, schedule_all

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

COMMANDS = [
    ("start", handlers.start),
    ("help", handlers.help_command),
    ("menu", handlers.menu_command),
    ("study", handlers.study_command),
    ("news", handlers.news_command),
    ("weather", handlers.weather_command),
    ("stocks", handlers.stocks_command),
    ("movies", handlers.movies_command),
    ("books", handlers.books_command),
    ("songs", handlers.songs_command),
    ("recipe", handlers.recipe_command),
    ("translate", handlers.translate_command),
    ("ask", handlers.ask_command),
    ("reset", handlers.reset_command),
    ("email", handlers.email_command),
    ("remind", handlers.remind_command),
    ("todo", handlers.todo_command),
    ("setcity", handlers.setcity_command),
    ("settime", handlers.settime_command),
    ("digest", handlers.digest_command),
    ("files", handlers.files_command),
    ("read", handlers.read_command),
    ("open", handlers.open_command),
    ("shot", handlers.shot_command),
    ("install", handlers.install_command),
]


def main() -> None:
    db.init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    for name, fn in COMMANDS:
        application.add_handler(CommandHandler(name, fn))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.echo)
    )
    application.add_handler(MessageHandler(filters.PHOTO, handlers.photo))
    application.add_handler(CallbackQueryHandler(handlers.menu_button))

    schedule_all(application.job_queue)
    resume_reminders(application.job_queue)

    application.run_polling()


if __name__ == "__main__":
    main()
