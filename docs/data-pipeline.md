# Data Pipeline

InvestmentAI keeps the market-data path deliberately small and inspectable.

## Flow

```text
Client request
  -> FastAPI /api/stock/{symbol}
  -> MarketDataService
  -> TTL cache lookup
  -> Stooq price provider
  -> SEC EDGAR fundamentals provider
  -> derived ratios
  -> typed API response
```

## Sources

- Stooq provides latest available OHLCV price snapshots.
- SEC EDGAR Company Facts provides U.S. issuer fundamentals.
- Local Graham notes under `backend/db/data/graham_chunks.txt` support the RAG advisory path.

## Cache Policy

Market snapshots use an in-process TTL cache controlled by `MARKET_DATA_CACHE_TTL_SECONDS`.

Default: `300` seconds.

The cache is intentionally in-memory because the current app is a single-process research assistant. If the backend becomes multi-instance, move this cache to Redis or another shared low-latency store.

## Quality Rules

- Empty symbols fail fast.
- Price and fundamentals failures are isolated so partial data can still be returned.
- Derived ratios are nullable instead of fabricated.
- API responses expose `status`, `warning`, and `cache_status` so the frontend can show uncertainty.
