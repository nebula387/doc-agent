# Doc Agent — Legal Document AI Assistant

A Telegram bot that analyzes legal documents (PDF, DOCX, TXT) and answers questions about their content using LLM reasoning. Upload a contract, ask questions — get structured analysis.

## Live Demo

➡️ **[@Doc_helper](https://t.me/my_do_helper_bot)** — try it now

## What It Does

- Upload up to 5 documents simultaneously (PDF, DOCX, TXT)
- Ask questions about the documents in natural language
- Cross-reference document content with live web search
- Switch between fast and deep-reasoning models per request
- Voice input support

## Model Selection

| Mode | Model | Use case |
|------|-------|----------|
| `/fast` (default) | Llama 4 Maverick | Quick questions, summaries |
| `/smart` | Gemini 2.5 Pro | Complex multi-doc analysis |

## Tech Stack

- Python 3.10+ / aiogram 3.x
- OpenRouter (Llama 4, Gemini 2.5 Pro)
- Groq Whisper — voice input
- Tavily — web search for fact-checking
- PyMuPDF / python-docx — document parsing

## Project Structure
```
doc-agent/
├── bot.py           # commands, message flow
├── llm.py           # model calls via OpenRouter
├── documents.py     # document storage and parsing
├── search.py        # Tavily web search
├── voice.py         # speech-to-text
├── config.example.py
└── requirements.txt
```
## Quick Start

```bash
git clone https://github.com/nebula387/doc-agent.git
cd doc-agent
pip install -r requirements.txt
cp config.example.py config.py
python bot.py
```

## Related

- [pro-bot](https://github.com/nebula387/pro-bot) — multi-model AI assistant with smart routing