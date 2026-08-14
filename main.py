import logging

from telegram import BotCommand
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
    ("summarize", handlers.summarize_command),
    ("create", handlers.create_command),
    ("append", handlers.append_command),
    ("delete", handlers.delete_command),
    ("open", handlers.open_command),
    ("close", handlers.close_command),
    ("shot", handlers.shot_command),
    ("install", handlers.install_command),
    ("uninstall", handlers.uninstall_command),
]

COMMAND_DESCRIPTIONS = [
    ("start", "Welcome message"),
    ("help", "List all commands"),
    ("menu", "Buttons menu"),
    ("study", "How exam prep works"),
    ("news", "Headlines (topic or language)"),
    ("weather", "Weather for a city"),
    ("stocks", "Sensex, Nifty & crypto"),
    ("movies", "Now showing in India"),
    ("books", "Search books"),
    ("songs", "Song suggestions"),
    ("recipe", "Recipe ideas"),
    ("translate", "Translate text"),
    ("ask", "Chat with AI"),
    ("reset", "Clear chat memory"),
    ("email", "Email a message"),
    ("remind", "Set a reminder"),
    ("todo", "Manage todos"),
    ("setcity", "Save your city"),
    ("settime", "Set digest time"),
    ("digest", "Run morning digest"),
    ("files", "List folder on PC"),
    ("read", "Read a file on PC"),
    ("summarize", "Summarize a file"),
    ("create", "Create a new file"),
    ("append", "Append to a file"),
    ("delete", "Delete a file"),
    ("open", "Open an app"),
    ("close", "Close an app/window"),
    ("shot", "Take a screenshot"),
    ("install", "Install via winget"),
    ("uninstall", "Uninstall via winget"),
]


async def register_commands(app) -> None:
    await app.bot.set_my_commands(
        [BotCommand(name, desc) for name, desc in COMMAND_DESCRIPTIONS]
    )


def main() -> None:
    db.init_db()

    application = (
        Application.builder().token(BOT_TOKEN).post_init(register_commands).build()
    )

    for name, fn in COMMANDS:
        application.add_handler(CommandHandler(name, handlers.owner_only(fn)))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.owner_only(handlers.echo))
    )
    application.add_handler(MessageHandler(filters.PHOTO, handlers.owner_only(handlers.photo)))
    application.add_handler(CallbackQueryHandler(handlers.owner_only(handlers.menu_button)))

    schedule_all(application.job_queue)
    resume_reminders(application.job_queue)

    application.run_polling()


if __name__ == "__main__":
    main()
