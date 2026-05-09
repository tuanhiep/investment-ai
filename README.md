# InvestmentAI

InvestmentAI is a full-stack investment research workspace inspired by Benjamin Graham. It combines a FastAPI backend, a Graham-style AI/RAG advisory layer, Stooq + SEC EDGAR market evidence, and a React/Vite frontend built for asking disciplined investment questions.

This project is not financial advice. It is a research assistant that helps separate facts, assumptions, risks, and next steps.

## What It Does

- Answers investment questions with a stricter Graham-style framework: margin of safety, intrinsic value range, earnings stability, balance-sheet strength, investor temperament, and evidence quality.
- Retrieves sourced local knowledge from `backend/db/data/graham_chunks.txt` with lightweight TF-IDF vector scoring before asking the LLM.
- Detects ticker symbols in chat questions and injects current market evidence into the Benjamin Graham agent prompt.
- Uses an internal Graham control layer inspired by Khí Học Tổ Thiên to keep every answer anchored in invariant, voice, boundary, pushback, and closure.
- Works without an OpenAI key by returning a deterministic local fallback answer.
- Uses OpenAI when `OPENAI_API_KEY` is configured.
- Fetches free market snapshots by combining Stooq price data with SEC EDGAR company fundamentals.
- Returns source citations and the market snapshot used by the chat answer.
- Provides REST endpoints and a WebSocket chat endpoint.
- Ships a responsive React investment workspace with chat, sources, decision principles, and market metrics.

## Project Structure

```text
InvestmentAI/
├── backend/
│   ├── __init__.py               # Installable Python package
│   ├── api/routes.py              # REST and WebSocket routes
│   ├── agents/investment_advisor_prompt.py
│   ├── config/config.py           # Environment-driven settings
│   ├── db/data/graham_chunks.txt  # Local investment knowledge base
│   ├── services/                  # Advisor, retrieval, Stooq + SEC market data
│   ├── schemas.py                 # API models
│   └── main.py                    # FastAPI application
├── docs/
│   ├── data-pipeline.md
│   ├── deployment.md
│   └── threat-model.md
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

For development and tests, install the package from the repo root:

```bash
pip install -e ".[dev]"
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

Market data is intentionally built on free sources:

- Stooq for latest available OHLCV price data.
- SEC EDGAR Company Facts for U.S. company fundamentals such as EPS, revenue, net income, assets, liabilities, equity, and shares outstanding.

Market snapshots use a small in-process TTL cache controlled by `MARKET_DATA_CACHE_TTL_SECONDS`. When a chat question includes a ticker such as `AAPL` or `cổ phiếu MSFT`, the advisor attempts to fetch that snapshot before answering. If current market evidence is unavailable, the Graham agent is instructed to say so instead of estimating from stale memory. See `docs/data-pipeline.md`.

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

cd ..
python -m pytest
```

## Security Notes

Never commit API keys. Use environment variables or `backend/.env`, which is ignored by git.

See `docs/threat-model.md` and `docs/deployment.md` for the current production-hardening assumptions and release checklist.
