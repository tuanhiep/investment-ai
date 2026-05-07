from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from io import StringIO
from typing import Any

import requests

from backend.config.config import get_settings


STOOQ_QUOTE_URL = "https://stooq.com/q/l/"
SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"


def _to_float(value: object) -> float | None:
    try:
        return float(value) if value not in (None, "", "N/D") else None
    except (TypeError, ValueError):
        return None


def _to_int(value: object) -> int | None:
    try:
        return int(float(value)) if value not in (None, "", "N/D") else None
    except (TypeError, ValueError):
        return None


def _safe_divide(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


@dataclass(frozen=True)
class MarketPrice:
    symbol: str
    price: float
    open: float | None
    high: float | None
    low: float | None
    volume: int | None
    as_of: str | None
    currency: str = "USD"
    source: str = "Stooq"


@dataclass(frozen=True)
class CompanyFundamentals:
    symbol: str
    cik: str
    company_name: str | None
    eps: float | None
    roe: float | None
    revenue: float | None
    net_income: float | None
    assets: float | None
    liabilities: float | None
    equity: float | None
    shares_outstanding: float | None
    fiscal_period: str | None
    source: str = "SEC EDGAR"


class StooqPriceProvider:
    def __init__(self, timeout_seconds: float) -> None:
        self.timeout_seconds = timeout_seconds

    def get_price(self, symbol: str) -> MarketPrice | None:
        response = requests.get(
            STOOQ_QUOTE_URL,
            params={"s": self._to_stooq_symbol(symbol), "f": "sd2t2ohlcv", "h": "", "e": "csv"},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        rows = list(csv.DictReader(StringIO(response.text)))
        if not rows:
            return None

        row = rows[0]
        close = _to_float(row.get("Close"))
        if close is None:
            return None

        date = row.get("Date")
        time = row.get("Time")
        return MarketPrice(
            symbol=symbol,
            price=close,
            open=_to_float(row.get("Open")),
            high=_to_float(row.get("High")),
            low=_to_float(row.get("Low")),
            volume=_to_int(row.get("Volume")),
            as_of=f"{date} {time}".strip() if date or time else None,
        )

    @staticmethod
    def _to_stooq_symbol(symbol: str) -> str:
        if "." in symbol:
            return symbol.lower()
        return f"{symbol.lower()}.us"


class SecEdgarFundamentalProvider:
    def __init__(self, timeout_seconds: float, user_agent: str) -> None:
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": user_agent,
            }
        )

    def get_fundamentals(self, symbol: str) -> CompanyFundamentals | None:
        ticker_map = self._get_ticker_map()
        company = ticker_map.get(symbol.upper())
        if not company:
            return None

        cik = str(company["cik_str"]).zfill(10)
        response = self.session.get(
            SEC_COMPANY_FACTS_URL.format(cik=cik),
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        facts = payload.get("facts", {}).get("us-gaap", {})
        dei_facts = payload.get("facts", {}).get("dei", {})

        revenue = self._latest_value(facts, ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"], ["USD"])
        net_income = self._latest_value(facts, ["NetIncomeLoss"], ["USD"])
        assets = self._latest_value(facts, ["Assets"], ["USD"])
        liabilities = self._latest_value(facts, ["Liabilities"], ["USD"])
        equity = self._latest_value(
            facts,
            ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
            ["USD"],
        )
        eps = self._latest_value(facts, ["EarningsPerShareDiluted", "EarningsPerShareBasic"], ["USD/shares"])
        shares = self._latest_value(
            dei_facts,
            ["EntityCommonStockSharesOutstanding"],
            ["shares"],
            forms=("10-K", "10-Q", "8-K"),
        )
        fiscal_period = self._latest_period(facts, ["NetIncomeLoss", "Assets", "StockholdersEquity"])

        return CompanyFundamentals(
            symbol=symbol,
            cik=cik,
            company_name=payload.get("entityName") or company.get("title"),
            eps=eps,
            roe=_safe_divide(net_income, equity),
            revenue=revenue,
            net_income=net_income,
            assets=assets,
            liabilities=liabilities,
            equity=equity,
            shares_outstanding=shares,
            fiscal_period=fiscal_period,
        )

    @lru_cache(maxsize=1)
    def _get_ticker_map(self) -> dict[str, dict[str, Any]]:
        response = self.session.get(SEC_COMPANY_TICKERS_URL, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        return {item["ticker"].upper(): item for item in payload.values()}

    def _latest_value(
        self,
        facts: dict[str, Any],
        concepts: list[str],
        units: list[str],
        forms: tuple[str, ...] = ("10-K", "10-Q"),
    ) -> float | None:
        fact = self._latest_fact(facts, concepts, units, forms)
        return _to_float(fact.get("val")) if fact else None

    def _latest_period(self, facts: dict[str, Any], concepts: list[str]) -> str | None:
        fact = self._latest_fact(facts, concepts, ["USD", "USD/shares", "shares"], ("10-K", "10-Q"))
        if not fact:
            return None
        fiscal_year = fact.get("fy")
        fiscal_period = fact.get("fp")
        if fiscal_year and fiscal_period:
            return f"{fiscal_year} {fiscal_period}"
        return fact.get("end")

    @staticmethod
    def _latest_fact(
        facts: dict[str, Any],
        concepts: list[str],
        units: list[str],
        forms: tuple[str, ...],
    ) -> dict[str, Any] | None:
        candidates: list[dict[str, Any]] = []
        for concept in concepts:
            concept_units = facts.get(concept, {}).get("units", {})
            for unit in units:
                candidates.extend(
                    item
                    for item in concept_units.get(unit, [])
                    if item.get("form") in forms and item.get("val") not in (None, "")
                )

        candidates.sort(key=lambda item: (item.get("filed") or "", item.get("end") or ""), reverse=True)
        return candidates[0] if candidates else None


class MarketDataService:
    def __init__(self) -> None:
        settings = get_settings()
        self.price_provider = StooqPriceProvider(settings.market_data_timeout_seconds)
        self.fundamental_provider = SecEdgarFundamentalProvider(
            timeout_seconds=settings.market_data_timeout_seconds,
            user_agent=settings.sec_edgar_user_agent,
        )

    def get_stock_snapshot(self, symbol: str) -> dict[str, Any]:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("Stock symbol is required")

        snapshot: dict[str, Any] = {
            "symbol": normalized,
            "company_name": None,
            "price": None,
            "pe": None,
            "roe": None,
            "eps": None,
            "market_cap": None,
            "open": None,
            "high": None,
            "low": None,
            "volume": None,
            "as_of": None,
            "currency": None,
            "revenue": None,
            "net_income": None,
            "assets": None,
            "liabilities": None,
            "equity": None,
            "shares_outstanding": None,
            "fiscal_period": None,
            "source": "Stooq + SEC EDGAR",
            "status": "unavailable",
            "warning": None,
        }
        warnings: list[str] = []

        try:
            price = self.price_provider.get_price(normalized)
            if price:
                snapshot.update(
                    {
                        "price": price.price,
                        "open": price.open,
                        "high": price.high,
                        "low": price.low,
                        "volume": price.volume,
                        "as_of": price.as_of,
                        "currency": price.currency,
                    }
                )
        except Exception:
            warnings.append("Không lấy được dữ liệu giá từ Stooq.")

        try:
            fundamentals = self.fundamental_provider.get_fundamentals(normalized)
            if fundamentals:
                snapshot.update(
                    {
                        "company_name": fundamentals.company_name,
                        "eps": fundamentals.eps,
                        "roe": fundamentals.roe,
                        "revenue": fundamentals.revenue,
                        "net_income": fundamentals.net_income,
                        "assets": fundamentals.assets,
                        "liabilities": fundamentals.liabilities,
                        "equity": fundamentals.equity,
                        "shares_outstanding": fundamentals.shares_outstanding,
                        "fiscal_period": fundamentals.fiscal_period,
                    }
                )
        except Exception:
            warnings.append("Không lấy được dữ liệu fundamentals từ SEC EDGAR.")

        snapshot["pe"] = _safe_divide(snapshot["price"], snapshot["eps"])
        snapshot["market_cap"] = (
            snapshot["price"] * snapshot["shares_outstanding"]
            if snapshot["price"] is not None and snapshot["shares_outstanding"] is not None
            else None
        )

        has_price = snapshot["price"] is not None
        has_fundamentals = any(snapshot[key] is not None for key in ("eps", "roe", "revenue", "assets", "equity"))
        if has_price and has_fundamentals:
            snapshot["status"] = "available"
        elif has_price or has_fundamentals:
            snapshot["status"] = "partial"

        if warnings:
            snapshot["warning"] = " ".join(warnings)
        elif snapshot["status"] == "partial":
            snapshot["warning"] = "Dữ liệu đang một phần; một số chỉ số có thể là N/A."

        return snapshot


market_data_service = MarketDataService()
