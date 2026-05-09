# Threat Model

InvestmentAI is a research assistant, not a trading or financial-advice system.

## Assets

- OpenAI API key and provider credentials.
- User-submitted investment questions.
- Local knowledge files.
- Market-data API responses.
- Frontend session state.

## Trust Boundaries

- Browser to FastAPI API.
- FastAPI to OpenAI.
- FastAPI to Stooq and SEC EDGAR.
- Repository code to local `.env` secrets.

## Main Risks

- Prompt injection through user questions or retrieved context.
- Hallucinated investment recommendations presented as facts.
- Leaked API keys through committed `.env` files or logs.
- Stale, partial, or missing market data being treated as complete.
- Overly broad CORS in non-local deployments.
- Denial of service through large chat payloads or repeated market-data calls.

## Current Controls

- `.env` is ignored; `.env.example` documents expected variables.
- Chat requests have Pydantic length validation.
- Market data has timeout controls and TTL caching.
- Partial data is surfaced with warning fields.
- The assistant copy explicitly says it is not financial advice.
- CI builds frontend and validates backend import/test paths.

## Production Hardening

- Restrict `CORS_ORIGINS` to deployed frontend origins.
- Add structured logging without secret or prompt dumps.
- Add rate limiting per IP/session.
- Add request IDs and error metrics.
- Use managed secrets rather than local `.env`.
- Add abuse tests for prompt injection and oversized payloads.
