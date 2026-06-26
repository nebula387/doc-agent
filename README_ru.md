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
| --- | --- | --- |
| `/fast` (по умолч.) | `llama-3.3-70b-instruct:free` | 66K — самая стабильная |
| `/smart` | `nemotron-3-super-120b-a12b:free` | 262K — глубокий анализ |

Полная цепочка: `nemotron-super` → `llama-3.3-70b` → `nemotron-nano` → `gemma-3-27b` → `openrouter/free`

## Стек

| Компонент | Сервис | Стоимость |
| --- | --- | --- |
| LLM | [OpenRouter](https://openrouter.ai) free tier | Бесплатно |
| Распознавание речи | [Groq](https://console.groq.com) Whisper large-v3 | Бесплатно |
| Веб-поиск | [Tavily](https://tavily.com) | 1000 req/мес бесплатно |
| Telegram-фреймворк | aiogram 3.x | — |
| Парсинг документов | PyMuPDF, python-docx | — |

---

## Деплой на VPS (автодеплой через GitHub Actions)

### 1. Нужные API-ключи

| Ключ | Где получить |
| --- | --- |
| `TELEGRAM_TOKEN` | [@BotFather](https://t.me/BotFather) |
| `OPENROUTER_API_KEY` | [openrouter.ai/keys](https://openrouter.ai/keys) |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) |

### 2. GitHub Secrets

Перейди в **Settings → Secrets and variables → Actions** в репозитории и добавь:

| Secret | Значение |
| --- | --- |
| `VPS_HOST` | IP-адрес или домен VPS |
| `VPS_USER` | SSH-пользователь (например `ubuntu` или `root`) |
| `VPS_SSH_KEY` | Приватный SSH-ключ в формате base64 (см. ниже) |

Как закодировать SSH-ключ в base64:

```bash
# Linux/Mac
cat ~/.ssh/id_rsa | base64 -w 0

# Windows (PowerShell)
[Convert]::ToBase64String([IO.File]::ReadAllBytes("$env:USERPROFILE\.ssh\id_rsa"))
```

Публичный ключ должен быть добавлен в `~/.ssh/authorized_keys` на VPS.

### 3. Первоначальная настройка VPS (один раз)

Заходи по SSH на VPS и выполняй:

```bash
# Клонируй репозиторий
git clone https://github.com/nebula387/doc-agent.git ~/doc-agent
cd ~/doc-agent

# Создай виртуальное окружение и установи зависимости
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Создай файл с секретами
cat > ~/doc-agent/.env <<'EOF'
TELEGRAM_TOKEN=твой_токен
OPENROUTER_API_KEY=sk-or-...
GROQ_API_KEY=gsk_...
TAVILY_API_KEY=tvly-...
EOF
chmod 600 ~/doc-agent/.env
```

### 4. Создание systemd-сервиса

```bash
sudo tee /etc/systemd/system/doc-agent.service > /dev/null <<'EOF'
[Unit]
Description=Doc Agent Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/doc-agent
EnvironmentFile=/home/ubuntu/doc-agent/.env
ExecStart=/home/ubuntu/doc-agent/venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable doc-agent
sudo systemctl start doc-agent

# Проверить статус
sudo systemctl status doc-agent
```

Разреши деплой-пользователю перезапускать сервис без ввода пароля:

```bash
echo "ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart doc-agent" | sudo tee /etc/sudoers.d/doc-agent
```

### 5. Как работает автодеплой

Каждый `git push` в ветку `main` запускает `.github/workflows/deploy.yml`:

1. GitHub Actions подключается по SSH к VPS
2. Выполняет `git pull origin main`
3. Переустанавливает/обновляет зависимости
4. Перезапускает systemd-сервис

Файл `.env` на VPS **workflow никогда не трогает** — ключи остаются в безопасности.

### Полезные команды на VPS

```bash
# Смотреть логи в реальном времени
sudo journalctl -u doc-agent -f

# Ручной перезапуск
sudo systemctl restart doc-agent

# Статус сервиса
sudo systemctl status doc-agent
```

---

## Локальный запуск

```bash
git clone https://github.com/nebula387/doc-agent.git
cd doc-agent

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

export TELEGRAM_TOKEN=...
export OPENROUTER_API_KEY=...
export GROQ_API_KEY=...
export TAVILY_API_KEY=...

python bot.py
```

## Структура проекта

```text
doc-agent/
├── bot.py            # обработчики, команды, логика сообщений
├── llm.py            # OpenRouter клиент, цепочка fallback-моделей
├── documents.py      # хранение и парсинг PDF/DOCX/TXT
├── search.py         # поиск через Tavily
├── voice.py          # Groq Whisper, голосовой ввод
├── config.py         # читает секреты из env vars (не коммитить реальные ключи!)
├── config.example.py # шаблон для локальной разработки
├── requirements.txt
├── Dockerfile        # для деплоя на Hugging Face Spaces
└── .github/
    └── workflows/
        └── deploy.yml  # автодеплой на VPS при push в main
```

## Команды

| Команда | Описание |
| --- | --- |
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
