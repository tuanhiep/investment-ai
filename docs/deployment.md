# Deployment

This repo is ready for a simple two-service deployment:

- Backend: FastAPI container.
- Frontend: static Vite build served by a CDN or platform static hosting.

## Backend

Recommended container command:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Required environment:

```text
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
SEC_EDGAR_USER_AGENT=InvestmentAI/1.0 you@example.com
MARKET_DATA_TIMEOUT_SECONDS=8
MARKET_DATA_CACHE_TTL_SECONDS=300
INVESTMENTAI_USE_MOCK_DATA=false
# Optional: point to a private prompt file mounted as a secret.
INVESTMENTAI_SYSTEM_PROMPT_FILE=
INVESTMENTAI_TIMEOUT_SECONDS=30
```

The backend runs without `OPENAI_API_KEY` in local fallback mode, but production should treat missing AI credentials as a degraded state.

## Frontend

Build:

```bash
cd frontend
npm ci
npm run build
```

Deploy `frontend/dist` to static hosting. Configure the API base URL or reverse proxy so `/api` and `/ws` reach the backend.

## Release Checklist

- CI green on backend tests and frontend build.
- Dependabot alerts reviewed.
- Production CORS origin configured.
- Secrets stored in platform secret manager.
- Private prompt overrides mounted from the secret manager, never baked into the image.
- `INVESTMENTAI_USE_MOCK_DATA=false` in production.
- Health endpoint checked: `GET /api/health`.
- Smoke test `POST /api/chat` and `GET /api/stock/AAPL`.
