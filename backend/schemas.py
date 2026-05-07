from pydantic import BaseModel, Field


class SourceDocument(BaseModel):
    title: str
    summary: str
    quote: str | None = None
    score: float = 0


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[SourceDocument] = []
    mode: str


class StockSnapshot(BaseModel):
    symbol: str
    company_name: str | None = None
    price: float | None = None
    pe: float | None = None
    roe: float | None = None
    eps: float | None = None
    market_cap: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    volume: int | None = None
    as_of: str | None = None
    currency: str | None = None
    revenue: float | None = None
    net_income: float | None = None
    assets: float | None = None
    liabilities: float | None = None
    equity: float | None = None
    shares_outstanding: float | None = None
    fiscal_period: str | None = None
    source: str = "Stooq + SEC EDGAR"
    status: str = "available"
    warning: str | None = None


class HealthResponse(BaseModel):
    status: str
    app: str
    ai_enabled: bool
