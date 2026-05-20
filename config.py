import os
import sys

TELEGRAM_TOKEN     = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY       = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY     = os.getenv("TAVILY_API_KEY")

BOT_NAMES = ["юрист", "бот", "агент"]

_missing = [k for k, v in {
    "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
    "OPENROUTER_API_KEY": OPENROUTER_API_KEY,
    "GROQ_API_KEY": GROQ_API_KEY,
    "TAVILY_API_KEY": TAVILY_API_KEY,
}.items() if not v]

if _missing:
    print(f"[config] Не заданы переменные окружения: {', '.join(_missing)}", file=sys.stderr)
    sys.exit(1)
