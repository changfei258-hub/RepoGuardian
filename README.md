# 🛡️ RepoGuardian

> AI-powered open-source maintainer — analyzes issues, reviews PRs, keeps your repo healthy.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)

---

## ✨ Features

| Feature | Status | Description |
|---------|--------|-------------|
| 🐛 Issue Analysis | ✅ | AI classifies, prioritizes, and auto-replies to issues |
| 📋 PR Review | ✅ | AI reviews pull requests and leaves comments |
| 🔄 Auto-labeling | 🔜 | Apply labels based on content |
| 📊 Dashboard | 🔜 | Web UI to manage your repos |
| 🌐 Multi-repo | 🔜 | Watch multiple repos at once |

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/changfei258-hub/RepoGuardian.git
cd RepoGuardian

# 2. Setup Python env
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install deps
cd backend
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Then edit .env — add your AI_API_KEY and GITHUB_TOKEN

# 5. Run
uvicorn app.main:app --reload
```

Open http://localhost:8000 — you should see the API running.

---

### 🤖 GitHub App Setup

1. Go to **Settings → Developer settings → GitHub Apps → New GitHub App**
2. Fill in:

   | Field | Value |
   |---|---|
   | App name | `RepoGuardian` |
   | Homepage URL | `https://github.com/changfei258-hub/RepoGuardian` |
   | Webhook URL | `https://your-domain.ngrok.io/webhook` (dev) |
   | Webhook secret | Generate one & save to `.env` |

3. Enable permissions:
   - **Issues**: Read & Write
   - **Pull requests**: Read & Write
   - **Metadata**: Read-only

4. Subscribe to events:
   - `Issues`
   - `Issue comment`
   - `Pull request`

5. Install the app on your repos.

---

## 🏗️ Project Structure

```
RepoGuardian/
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI server
│   │   ├── webhook.py     # GitHub webhook handler
│   │   ├── ai.py          # AI analysis (OpenAI)
│   │   ├── github.py      # GitHub API client
│   │   ├── database.py    # SQLAlchemy models
│   │   └── config.py      # Settings
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/              # Dashboard (coming)
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 📄 License

MIT — do what you want, just give credit.

---

<p align="center">Built with ❤️ by <a href="https://github.com/changfei258-hub">changfei258-hub</a></p>
