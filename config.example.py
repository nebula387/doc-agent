import os

# Читаем из переменных окружения (для Hugging Face Spaces / продакшена)
# Локально: задай переменные окружения или замени None на строки с ключами
TELEGRAM_TOKEN     = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY       = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY     = os.getenv("TAVILY_API_KEY")

# Имена бота в групповом чате
BOT_NAMES = ["юрист", "бот", "агент"]
