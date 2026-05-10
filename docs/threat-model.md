# Threat Model

InvestmentAI is a research assistant, not a trading or financial-advice system.

## Assets

- OpenAI API key and provider credentials.
- User-submitted investment questions.
- Local knowledge files.
- Private system prompt overrides.
- Market-data API responses.
- Frontend session state.

## Trust Boundaries

- Browser to FastAPI API.
- FastAPI to OpenAI.
- FastAPI to Stooq and SEC EDGAR.
- Repository code to local `.env` secrets.
- Public baseline prompt to private deployment prompt.

## Main Risks

- Prompt injection through user questions or retrieved context.
- Hallucinated investment recommendations presented as facts.
- Leaked API keys through committed `.env` files or logs.
- Leaked proprietary prompt or investment operating contract through committed config files.
- Stale, partial, or missing market data being treated as complete.
- Overly broad CORS in non-local deployments.
- Denial of service through large chat payloads or repeated market-data calls.

## Current Controls

- `.env` is ignored; `.env.example` documents expected variables.
- `backend/config/prompts/*.local.md` is ignored; public prompt examples remain runnable.
- Mock market-data mode supports demos without live provider access.
- Chat requests have Pydantic length validation.
- Market data has timeout controls and TTL caching.
- Partial data is surfaced with warning fields.
- Decision-state and evidence-score outputs make uncertainty explicit instead of hiding it in prose.
- The assistant copy explicitly says it is not financial advice.
- CI builds frontend and validates backend import/test paths.

## Production Hardening

- Restrict `CORS_ORIGINS` to deployed frontend origins.
- Add structured logging without secret or prompt dumps.
- Add rate limiting per IP/session.
- Add request IDs and error metrics.
- Use managed secrets rather than local `.env`.
- Mount private prompt files or provide prompt text through a secret-backed config channel.
- Add abuse tests for prompt injection and oversized payloads.
