import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

if not BOT_TOKEN or BOT_TOKEN == "your_token_here":
    raise SystemExit(
        "BOT_TOKEN is not set. Open the .env file in this folder and paste "
        "your BotFather token next to BOT_TOKEN=, then run py main.py again."
    )

# LLM providers (free tiers, all OpenAI-compatible). Cascade order: Gemini -> Groq -> Cerebras -> GLM.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "").strip()
ZAI_API_KEY = os.getenv("ZAI_API_KEY", "").strip()

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "").strip()

# Email (Gmail SMTP + App Password)
GMAIL_USER = os.getenv("GMAIL_USER", "").strip()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").strip()

# Desktop control gate: DESKTOP_CONTROL=1 enables /files /read /open /shot /install
# Only works for OWNER_ID (comma-separated Telegram user IDs).
DESKTOP_CONTROL = os.getenv("DESKTOP_CONTROL", "0").strip() == "1"
OWNER_IDS = [x.strip() for x in os.getenv("OWNER_ID", "").split(",") if x.strip()]


def is_owner(chat_id) -> bool:
    return str(chat_id) in OWNER_IDS
