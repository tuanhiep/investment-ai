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

For chat requests, the advisor also runs a ticker-detection pass:

```text
Client question
  -> FastAPI /api/chat
  -> InvestmentAdvisor
  -> Graham knowledge retrieval
  -> ticker detection
  -> MarketDataService when a ticker is present
  -> GrahamQiControl judgment layer
  -> prompt with knowledge context + current market evidence
  -> answer with sources + market_snapshot
```

## Sources

- Stooq provides latest available OHLCV price snapshots.
- SEC EDGAR Company Facts provides U.S. issuer fundamentals.
- Local Graham notes under `backend/db/data/graham_chunks.txt` support the RAG advisory path. Each chunk includes a source and source type so responses can distinguish Graham primary texts, historical practice, SEC filings, and market data.

## Cache Policy

Market snapshots use an in-process TTL cache controlled by `MARKET_DATA_CACHE_TTL_SECONDS`.

Default: `300` seconds.

The cache is intentionally in-memory because the current app is a single-process research assistant. If the backend becomes multi-instance, move this cache to Redis or another shared low-latency store.

## Quality Rules

- Empty symbols fail fast.
- Price and fundamentals failures are isolated so partial data can still be returned.
- Derived ratios are nullable instead of fabricated.
- API responses expose `status`, `warning`, and `cache_status` so the frontend can show uncertainty.
- Chat answers must not substitute memory for current market evidence. If ticker-specific data cannot be retrieved, the answer should state the retrieval failure and continue only with principles and a research checklist.
- Retrieval uses local TF-IDF vector scoring plus keyword/title boosts. This keeps the MVP dependency-light while improving over plain token overlap.
- The Graham judgment layer uses Khí Học Tổ Thiên as an internal control plane: `Tru` for invariants, `Tanh` for voice, `Gioi` for boundaries, `Phan` for pushback, and `Hoi` for closure. It does not replace financial evidence; it keeps the Graham answer disciplined, human, and decisive.
