from typing import Any

from pydantic import BaseModel, Field


class SourceDocument(BaseModel):
    title: str
    summary: str
    quote: str | None = None
    source: str | None = None
    source_type: str | None = None
    score: float = 0


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[SourceDocument] = Field(default_factory=list)
    mode: str
    market_snapshot: dict[str, Any] | None = None


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
    current_assets: float | None = None
    current_liabilities: float | None = None
    cash_and_equivalents: float | None = None
    total_debt: float | None = None
    operating_cash_flow: float | None = None
    capital_expenditures: float | None = None
    free_cash_flow: float | None = None
    current_ratio: float | None = None
    debt_to_equity: float | None = None
    working_capital: float | None = None
    annual_history: list[dict[str, Any]] = Field(default_factory=list)
    earnings_years: int | None = None
    positive_earnings_years: int | None = None
    latest_annual_revenue: float | None = None
    oldest_annual_revenue: float | None = None
    latest_annual_eps: float | None = None
    oldest_annual_eps: float | None = None
    fiscal_period: str | None = None
    source: str = "Stooq + SEC EDGAR"
    status: str = "available"
    warning: str | None = None
    cache_status: str = "miss"


class HealthResponse(BaseModel):
    status: str
    app: str
    ai_enabled: bool
