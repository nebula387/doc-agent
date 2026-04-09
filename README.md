---
title: Doc Agent
emoji: ⚖️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Doc Agent — Legal AI Assistant

A Telegram bot that analyzes legal documents and answers questions about law using a **free LLM fallback chain** via OpenRouter. Upload a contract, get a structured breakdown, cross-check with live web search.

**Live demo:** [@Doc_helper](https://t.me/my_do_helper_bot)

---

## Features

- **Document analysis** — upload up to 5 files (PDF, DOCX, TXT), ask questions about their content
- **Legal Q&A** — works without documents too, answers questions about legislation
- **Web fact-checking** — "Check online" button on every answer (Tavily search)
- **Voice input** — send a voice message, the bot transcribes it via Groq Whisper
- **Conversation memory** — 1-hour context window, reset with `/new`
- **Free model fallback chain** — if one model is rate-limited, the next one picks up automatically

## Model Strategy

All models are **100% free** via OpenRouter. The bot tries them in priority order — if one is unavailable or rate-limited, it falls back to the next automatically.

| Mode | Primary model | Context |
|------|--------------|---------|
| `/fast` (default) | `llama-3.3-70b-instruct:free` | 66K — most stable |
| `/smart` | `nemotron-3-super-120b-a12b:free` | 262K — deeper reasoning |

Full fallback chain: `nemotron-super` → `llama-3.3-70b` → `nemotron-nano` → `gemma-3-27b` → `openrouter/free`

## Tech Stack

| Component | Service | Cost |
|-----------|---------|------|
| LLM | [OpenRouter](https://openrouter.ai) — free tier | Free |
| Voice STT | [Groq](https://console.groq.com) Whisper large-v3 | Free |
| Web search | [Tavily](https://tavily.com) | 1000 req/mo free |
| Bot framework | aiogram 3.x | — |
| Doc parsing | PyMuPDF, python-docx | — |

## Deploy on Hugging Face Spaces

1. Fork this repo or create a new Space (Docker SDK)
2. Add the following **Secrets** in Space Settings:

   | Secret | Where to get |
   |--------|-------------|
   | `TELEGRAM_TOKEN` | [@BotFather](https://t.me/BotFather) |
   | `OPENROUTER_API_KEY` | [openrouter.ai/keys](https://openrouter.ai/keys) |
   | `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) |
   | `TAVILY_API_KEY` | [tavily.com](https://tavily.com) |

3. The Space will start automatically — the bot uses long polling, no webhook setup needed.

> **Note:** Hugging Face Spaces sleep after inactivity on the free tier. For 24/7 uptime, upgrade to a persistent Space or use an external runner.

## Local Setup

```bash
git clone https://github.com/nebula387/doc-agent.git
cd doc-agent

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Set environment variables (or copy config.example.py to config.py and fill in values)
export TELEGRAM_TOKEN=...
export OPENROUTER_API_KEY=...
export GROQ_API_KEY=...
export TAVILY_API_KEY=...

python bot.py
```

## Project Structure

```
doc-agent/
├── bot.py            # Telegram handlers, command routing, message flow
├── llm.py            # OpenRouter client, free model fallback chain
├── documents.py      # In-memory document storage, PDF/DOCX/TXT parsing
├── search.py         # Tavily web search integration
├── voice.py          # Groq Whisper speech-to-text
├── config.py         # Reads secrets from env vars (never commit real keys)
├── config.example.py # Template for local development
└── requirements.txt
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Full command reference |
| `/smart` | Switch to deep-reasoning model |
| `/fast` | Switch to fast stable model (default) |
| `/model` | Show current model |
| `/new` | Reset conversation context |
| `/docs` | List uploaded documents |
| `/deldoc filename.pdf` | Remove a specific document |
| `/cleardocs` | Remove all documents |

> ⚠️ This bot provides general legal information only. It does not replace professional legal advice.

## License

MIT
