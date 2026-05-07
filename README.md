# InvestmentAI

InvestmentAI is a full-stack investment research workspace inspired by Benjamin Graham. It combines a FastAPI backend, an AI/RAG advisory layer, Yahoo Finance snapshots, and a React/Vite frontend built for asking disciplined investment questions.

This project is not financial advice. It is a research assistant that helps separate facts, assumptions, risks, and next steps.

## What It Does

- Answers investment questions with a Graham-style framework: margin of safety, intrinsic value, earnings stability, temperament, and evidence quality.
- Retrieves local knowledge from `backend/db/data/graham_chunks.txt` before asking the LLM.
- Works without an OpenAI key by returning a deterministic local fallback answer.
- Uses OpenAI when `OPENAI_API_KEY` is configured.
- Fetches ticker snapshots through Yahoo Finance.
- Provides REST endpoints and a WebSocket chat endpoint.
- Ships a responsive React investment workspace with chat, sources, decision principles, and market metrics.

## Project Structure

```text
InvestmentAI/
├── backend/
│   ├── api/routes.py              # REST and WebSocket routes
│   ├── agents/prompt_graham.py    # Advisor prompt contract
│   ├── config/config.py           # Environment-driven settings
│   ├── db/data/graham_chunks.txt  # Local investment knowledge base
│   ├── services/                  # Advisor, retrieval, market data
│   ├── schemas.py                 # API models
│   └── main.py                    # FastAPI application
├── frontend/
│   ├── src/App.tsx                # Investment workspace
│   ├── src/App.css
│   └── vite.config.ts             # API and WebSocket proxy
└── launch.py                      # Backend launcher
```

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `OPENAI_API_KEY` in `backend/.env` or your shell if you want LLM answers. Without it, the backend still runs in local fallback mode.

```bash
cd ..
uvicorn backend.main:app --reload
```

Backend runs on `http://127.0.0.1:8000`.

Useful endpoints:

- `GET /api/health`
- `POST /api/chat`
- `GET /api/stock/{symbol}`
- `WS /ws/chat`

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173` and proxies `/api` and `/ws` to the backend.

## Development Checks

```bash
cd frontend
npm run build

cd ../backend
python -m compileall .
```

## Security Notes

Never commit API keys. Use environment variables or `backend/.env`, which is ignored by git.
