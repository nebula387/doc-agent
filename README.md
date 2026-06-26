# Doc Agent — Legal AI Assistant

A Telegram bot that analyzes legal documents and answers questions about law using a **free LLM fallback chain** via OpenRouter. Upload a contract, get a structured breakdown, cross-check with live web search.

**Try it:** [@Doc_helper](https://t.me/doc_agent_hf_bot)

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
| --- | --- | --- |
| `/fast` (default) | `llama-3.3-70b-instruct:free` | 66K — most stable |
| `/smart` | `nemotron-3-super-120b-a12b:free` | 262K — deeper reasoning |

Full fallback chain: `nemotron-super` → `llama-3.3-70b` → `nemotron-nano` → `gemma-3-27b` → `openrouter/free`

## Tech Stack

| Component | Service | Cost |
| --- | --- | --- |
| LLM | [OpenRouter](https://openrouter.ai) — free tier | Free |
| Voice STT | [Groq](https://console.groq.com) Whisper large-v3 | Free |
| Web search | [Tavily](https://tavily.com) | 1000 req/mo free |
| Bot framework | aiogram 3.x | — |
| Doc parsing | PyMuPDF, python-docx | — |

## Bot Commands

| Command | Description |
| --- | --- |
| `/start` | Welcome message |
| `/help` | Full command reference |
| `/smart` | Switch to deep-reasoning model |
| `/fast` | Switch to fast stable model (default) |
| `/model` | Show current model |
| `/new` | Reset conversation context |
| `/docs` | List uploaded documents |
| `/deldoc filename.pdf` | Remove a specific document |
| `/cleardocs` | Remove all documents |

---

## Deploy to VPS (auto-deploy via GitHub Actions)

### 1. API keys you need

| Key | Where to get |
| --- | --- |
| `TELEGRAM_TOKEN` | [@BotFather](https://t.me/BotFather) |
| `OPENROUTER_API_KEY` | [openrouter.ai/keys](https://openrouter.ai/keys) |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) |

### 2. GitHub Secrets

Go to **Settings → Secrets and variables → Actions** in your repo and add:

| Secret | Value |
| --- | --- |
| `VPS_HOST` | IP address or hostname of your VPS |
| `VPS_USER` | SSH username (e.g. `ubuntu` or `root`) |
| `VPS_SSH_KEY` | Private SSH key, base64-encoded (see below) |

To base64-encode your SSH private key:

```bash
# On Linux/Mac
cat ~/.ssh/id_rsa | base64 -w 0

# On Windows (PowerShell)
[Convert]::ToBase64String([IO.File]::ReadAllBytes("$env:USERPROFILE\.ssh\id_rsa"))
```

The **public key** must be added to `~/.ssh/authorized_keys` on the VPS.

### 3. First-time VPS setup

SSH into your VPS and run:

```bash
# Clone the repo
git clone https://github.com/nebula387/doc-agent.git ~/doc-agent
cd ~/doc-agent

# Create virtualenv and install deps
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create the .env file with your secrets
cat > ~/doc-agent/.env <<'EOF'
TELEGRAM_TOKEN=your_token_here
OPENROUTER_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
EOF
chmod 600 ~/doc-agent/.env
```

### 4. Create systemd service

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

# Check status
sudo systemctl status doc-agent
```

Allow the deploy user to restart the service without a password prompt:

```bash
echo "ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart doc-agent" | sudo tee /etc/sudoers.d/doc-agent
```

### 5. How auto-deploy works

Every push to `main` triggers `.github/workflows/deploy.yml`:

1. GitHub Actions SSH-es into the VPS
2. Runs `git pull origin main`
3. Reinstalls/upgrades Python dependencies
4. Restarts the systemd service

The `.env` file on the VPS is **never touched** by the workflow — secrets stay safe.

### Useful VPS commands

```bash
# View live logs
sudo journalctl -u doc-agent -f

# Manual restart
sudo systemctl restart doc-agent

# Check status
sudo systemctl status doc-agent
```

---

## Local Setup

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

## Project Structure

```text
doc-agent/
├── bot.py            # Telegram handlers, command routing, message flow
├── llm.py            # OpenRouter client, free model fallback chain
├── documents.py      # In-memory document storage, PDF/DOCX/TXT parsing
├── search.py         # Tavily web search integration
├── voice.py          # Groq Whisper speech-to-text
├── config.py         # Reads secrets from env vars (never commit real keys)
├── config.example.py # Template for local development
├── requirements.txt
├── Dockerfile        # For Hugging Face Spaces deployment
└── .github/
    └── workflows/
        └── deploy.yml  # Auto-deploy to VPS on push to main
```

---

> ⚠️ This bot provides general legal information only. It does not replace professional legal advice.

## License

MIT
