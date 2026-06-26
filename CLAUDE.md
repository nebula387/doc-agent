# Doc Agent — CLAUDE.md

## Project overview

Telegram bot for legal document analysis and Q&A. Uses a free LLM fallback chain via OpenRouter, web search via Tavily, and voice transcription via Groq Whisper. Deployed as a systemd service on VPS.

## File structure

```
bot.py          — Telegram handlers, message routing, formatting (md_to_html, normalize_llm_output)
llm.py          — OpenRouter client, FREE_MODELS list, fallback chain logic
documents.py    — In-memory per-user document store; PDF/DOCX/TXT parsing
search.py       — Tavily web search (legal_search)
voice.py        — Groq Whisper transcription
config.py       — Reads all secrets from env vars (never commit real keys)
config.example.py  — Template for local dev
requirements.txt
Dockerfile      — python:3.11-slim, used for HuggingFace Spaces
.github/workflows/deploy.yml  — SSH-based auto-deploy to VPS on push to main
```

## Run locally

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set env vars or copy config.example.py → config.py and fill in values
export TELEGRAM_TOKEN=...
export OPENROUTER_API_KEY=...
export GROQ_API_KEY=...
export TAVILY_API_KEY=...

python bot.py
```

## Environment variables

| Variable | Source |
|---|---|
| `TELEGRAM_TOKEN` | @BotFather |
| `OPENROUTER_API_KEY` | openrouter.ai/keys |
| `GROQ_API_KEY` | console.groq.com |
| `TAVILY_API_KEY` | tavily.com |

## Deploy (VPS + systemd)

Auto-deploy triggers on every push to `main` via `.github/workflows/deploy.yml`.
The workflow SSH-es into the VPS, runs `git pull`, reinstalls deps, restarts the service.

GitHub Secrets required: `VPS_SSH_KEY` (base64-encoded private key), `VPS_HOST`, `VPS_USER`.

The bot runs under systemd as `doc-agent`. The service reads env vars from `~/doc-agent/.env`.

## Key conventions

- User state is in-memory (`user_state` dict in bot.py) — restarts clear all sessions/documents by design.
- LLM models are free-tier via OpenRouter; fallback order is defined in `llm.py:FREE_MODELS`.
- All Telegram messages use `parse_mode="HTML"`. Markdown from LLM is converted via `md_to_html()` in bot.py.
- Groups: bot responds only when mentioned by `@username`, by name (`BOT_NAMES`), or in reply to itself.
