# Doc Agent — Юридический ИИ-ассистент

Telegram-бот для анализа юридических документов и консультаций по праву. Работает на **цепочке бесплатных LLM** через OpenRouter — если одна модель недоступна, автоматически переключается на следующую.

**Демо:** [@Doc_helper](https://t.me/my_do_helper_bot)

---

## Возможности

- **Анализ документов** — до 5 файлов одновременно (PDF, DOCX, TXT), вопросы по содержимому
- **Консультации без документа** — отвечает на вопросы по законодательству
- **Проверка в интернете** — кнопка под каждым ответом (поиск через Tavily)
- **Голосовой ввод** — распознавание речи через Groq Whisper
- **Память разговора** — контекст сохраняется 1 час, сброс через `/new`
- **Автоматический fallback** — если модель перегружена, бот переключается на следующую

## Модели

Все модели **бесплатные** через OpenRouter. При ошибке или rate limit бот пробует следующую по цепочке.

| Режим | Основная модель | Контекст |
|-------|----------------|---------|
| `/fast` (по умолч.) | `llama-3.3-70b-instruct:free` | 66K — самая стабильная |
| `/smart` | `nemotron-3-super-120b-a12b:free` | 262K — глубокий анализ |

Полная цепочка: `nemotron-super` → `llama-3.3-70b` → `nemotron-nano` → `gemma-3-27b` → `openrouter/free`

## Стек

| Компонент | Сервис | Стоимость |
|-----------|--------|-----------|
| LLM | [OpenRouter](https://openrouter.ai) free tier | Бесплатно |
| Распознавание речи | [Groq](https://console.groq.com) Whisper large-v3 | Бесплатно |
| Веб-поиск | [Tavily](https://tavily.com) | 1000 req/мес бесплатно |
| Telegram-фреймворк | aiogram 3.x | — |
| Парсинг документов | PyMuPDF, python-docx | — |

## Деплой на Hugging Face Spaces

1. Форкни репозиторий или создай новый Space (Docker SDK)
2. В настройках Space добавь **Secrets**:

   | Секрет | Где получить |
   |--------|-------------|
   | `TELEGRAM_TOKEN` | [@BotFather](https://t.me/BotFather) |
   | `OPENROUTER_API_KEY` | [openrouter.ai/keys](https://openrouter.ai/keys) |
   | `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) |
   | `TAVILY_API_KEY` | [tavily.com](https://tavily.com) |

3. Space запустится автоматически — бот использует long polling, webhook не нужен.

> **Важно:** Free-tier Spaces на HF засыпают при неактивности. Для 24/7 работы нужен платный Space или внешний хостинг.

## Локальный запуск

```bash
git clone https://github.com/nebula387/doc-agent.git
cd doc-agent

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Задай переменные окружения (или скопируй config.example.py в config.py и заполни)
export TELEGRAM_TOKEN=...
export OPENROUTER_API_KEY=...
export GROQ_API_KEY=...
export TAVILY_API_KEY=...

python bot.py
```

## Структура проекта

```
doc-agent/
├── bot.py            # обработчики, команды, логика сообщений
├── llm.py            # OpenRouter клиент, цепочка fallback-моделей
├── documents.py      # хранение и парсинг PDF/DOCX/TXT
├── search.py         # поиск через Tavily
├── voice.py          # Groq Whisper, голосовой ввод
├── config.py         # читает секреты из env vars (не коммитить реальные ключи!)
├── config.example.py # шаблон для локальной разработки
└── requirements.txt
```

## Команды

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие |
| `/help` | Полная справка |
| `/smart` | Переключить на мощную модель |
| `/fast` | Переключить на быструю модель (по умолч.) |
| `/model` | Текущая модель |
| `/new` | Сбросить контекст разговора |
| `/docs` | Список загруженных документов |
| `/deldoc имя.pdf` | Удалить конкретный файл |
| `/cleardocs` | Удалить все документы |

> ⚠️ Бот предоставляет информацию общего характера. Не заменяет профессионального юриста.

## Лицензия

MIT
