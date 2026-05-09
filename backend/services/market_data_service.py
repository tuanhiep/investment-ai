from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from io import StringIO
from time import monotonic
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
    annual_history: list[dict[str, Any]] | None = None
    earnings_years: int | None = None
    positive_earnings_years: int | None = None
    latest_annual_revenue: float | None = None
    oldest_annual_revenue: float | None = None
    latest_annual_eps: float | None = None
    oldest_annual_eps: float | None = None
    source: str = "SEC EDGAR"


@dataclass
class CacheEntry:
    value: dict[str, Any]
    expires_at: float


class TtlCache:
    def __init__(self, ttl_seconds: float, clock: Any = monotonic) -> None:
        self.ttl_seconds = ttl_seconds
        self.clock = clock
        self._values: dict[str, CacheEntry] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        entry = self._values.get(key)
        if not entry:
            return None
        if entry.expires_at <= self.clock():
            self._values.pop(key, None)
            return None
        return dict(entry.value)

    def set(self, key: str, value: dict[str, Any]) -> None:
        if self.ttl_seconds <= 0:
            return
        self._values[key] = CacheEntry(value=dict(value), expires_at=self.clock() + self.ttl_seconds)

    def clear(self) -> None:
        self._values.clear()


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
        current_assets = self._latest_value(facts, ["AssetsCurrent"], ["USD"])
        current_liabilities = self._latest_value(facts, ["LiabilitiesCurrent"], ["USD"])
        cash = self._latest_value(
            facts,
            [
                "CashAndCashEquivalentsAtCarryingValue",
                "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
            ],
            ["USD"],
        )
        long_term_debt = self._latest_value(
            facts,
            [
                "LongTermDebtAndFinanceLeaseObligationsCurrentAndNoncurrent",
                "LongTermDebtAndCapitalLeaseObligations",
                "LongTermDebt",
            ],
            ["USD"],
        )
        short_term_debt = self._latest_value(
            facts,
            ["ShortTermBorrowings", "ShortTermDebtCurrent", "LongTermDebtCurrent"],
            ["USD"],
        )
        operating_cash_flow = self._latest_value(
            facts,
            ["NetCashProvidedByUsedInOperatingActivities"],
            ["USD"],
        )
        capex = self._latest_value(
            facts,
            ["PaymentsToAcquirePropertyPlantAndEquipment"],
            ["USD"],
        )
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
        annual_history = self._annual_history(facts)
        positive_earnings_years = sum(
            1
            for row in annual_history
            if isinstance(row.get("net_income"), int | float) and row["net_income"] > 0
        )

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
            current_assets=current_assets,
            current_liabilities=current_liabilities,
            cash_and_equivalents=cash,
            total_debt=(long_term_debt or 0) + (short_term_debt or 0)
            if long_term_debt is not None or short_term_debt is not None
            else None,
            operating_cash_flow=operating_cash_flow,
            capital_expenditures=capex,
            free_cash_flow=operating_cash_flow - abs(capex)
            if operating_cash_flow is not None and capex is not None
            else None,
            current_ratio=_safe_divide(current_assets, current_liabilities),
            debt_to_equity=_safe_divide(
                (long_term_debt or 0) + (short_term_debt or 0)
                if long_term_debt is not None or short_term_debt is not None
                else None,
                equity,
            ),
            working_capital=current_assets - current_liabilities
            if current_assets is not None and current_liabilities is not None
            else None,
            annual_history=annual_history,
            earnings_years=len([row for row in annual_history if row.get("net_income") is not None]),
            positive_earnings_years=positive_earnings_years,
            latest_annual_revenue=self._history_value(annual_history, "revenue", newest=True),
            oldest_annual_revenue=self._history_value(annual_history, "revenue", newest=False),
            latest_annual_eps=self._history_value(annual_history, "eps", newest=True),
            oldest_annual_eps=self._history_value(annual_history, "eps", newest=False),
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

    def _annual_history(self, facts: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
        history: dict[int, dict[str, Any]] = {}
        for field, concepts, units in (
            ("revenue", ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"], ["USD"]),
            ("net_income", ["NetIncomeLoss"], ["USD"]),
            ("eps", ["EarningsPerShareDiluted", "EarningsPerShareBasic"], ["USD/shares"]),
            ("operating_cash_flow", ["NetCashProvidedByUsedInOperatingActivities"], ["USD"]),
            ("capital_expenditures", ["PaymentsToAcquirePropertyPlantAndEquipment"], ["USD"]),
        ):
            for fact in self._annual_facts(facts, concepts, units):
                year = _to_int(fact.get("fy"))
                value = _to_float(fact.get("val"))
                if year is None or value is None:
                    continue
                row = history.setdefault(year, {"year": year})
                row.setdefault(field, value)

        for row in history.values():
            operating_cash_flow = row.get("operating_cash_flow")
            capex = row.get("capital_expenditures")
            row["free_cash_flow"] = (
                operating_cash_flow - abs(capex)
                if isinstance(operating_cash_flow, int | float) and isinstance(capex, int | float)
                else None
            )

        return sorted(history.values(), key=lambda item: item["year"], reverse=True)[:limit]

    @staticmethod
    def _history_value(history: list[dict[str, Any]], field: str, newest: bool) -> float | None:
        rows = history if newest else list(reversed(history))
        for row in rows:
            value = row.get(field)
            if isinstance(value, int | float):
                return value
        return None

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

    @staticmethod
    def _annual_facts(
        facts: dict[str, Any],
        concepts: list[str],
        units: list[str],
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        for concept in concepts:
            concept_units = facts.get(concept, {}).get("units", {})
            for unit in units:
                candidates.extend(
                    item
                    for item in concept_units.get(unit, [])
                    if item.get("form") == "10-K" and item.get("fp") == "FY" and item.get("val") not in (None, "")
                )

        candidates.sort(key=lambda item: (item.get("fy") or 0, item.get("filed") or ""), reverse=True)
        deduped: dict[int, dict[str, Any]] = {}
        for item in candidates:
            year = _to_int(item.get("fy"))
            if year is not None and year not in deduped:
                deduped[year] = item
        return list(deduped.values())


class MarketDataService:
    def __init__(
        self,
        price_provider: StooqPriceProvider | None = None,
        fundamental_provider: SecEdgarFundamentalProvider | None = None,
        cache: TtlCache | None = None,
    ) -> None:
        settings = get_settings()
        self.price_provider = price_provider or StooqPriceProvider(settings.market_data_timeout_seconds)
        self.fundamental_provider = fundamental_provider or SecEdgarFundamentalProvider(
            timeout_seconds=settings.market_data_timeout_seconds,
            user_agent=settings.sec_edgar_user_agent,
        )
        self.cache = cache or TtlCache(settings.market_data_cache_ttl_seconds)

    def get_stock_snapshot(self, symbol: str) -> dict[str, Any]:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("Stock symbol is required")

        cached = self.cache.get(normalized)
        if cached:
            cached["cache_status"] = "hit"
            return cached

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
            "current_assets": None,
            "current_liabilities": None,
            "cash_and_equivalents": None,
            "total_debt": None,
            "operating_cash_flow": None,
            "capital_expenditures": None,
            "free_cash_flow": None,
            "current_ratio": None,
            "debt_to_equity": None,
            "working_capital": None,
            "annual_history": [],
            "earnings_years": None,
            "positive_earnings_years": None,
            "latest_annual_revenue": None,
            "oldest_annual_revenue": None,
            "latest_annual_eps": None,
            "oldest_annual_eps": None,
            "fiscal_period": None,
            "source": "Stooq + SEC EDGAR",
            "status": "unavailable",
            "warning": None,
            "cache_status": "miss",
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
            warnings.append("Could not retrieve price data from Stooq.")

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
                        "current_assets": fundamentals.current_assets,
                        "current_liabilities": fundamentals.current_liabilities,
                        "cash_and_equivalents": fundamentals.cash_and_equivalents,
                        "total_debt": fundamentals.total_debt,
                        "operating_cash_flow": fundamentals.operating_cash_flow,
                        "capital_expenditures": fundamentals.capital_expenditures,
                        "free_cash_flow": fundamentals.free_cash_flow,
                        "current_ratio": fundamentals.current_ratio,
                        "debt_to_equity": fundamentals.debt_to_equity,
                        "working_capital": fundamentals.working_capital,
                        "annual_history": fundamentals.annual_history or [],
                        "earnings_years": fundamentals.earnings_years,
                        "positive_earnings_years": fundamentals.positive_earnings_years,
                        "latest_annual_revenue": fundamentals.latest_annual_revenue,
                        "oldest_annual_revenue": fundamentals.oldest_annual_revenue,
                        "latest_annual_eps": fundamentals.latest_annual_eps,
                        "oldest_annual_eps": fundamentals.oldest_annual_eps,
                        "fiscal_period": fundamentals.fiscal_period,
                    }
                )
        except Exception:
            warnings.append("Could not retrieve fundamentals from SEC EDGAR.")

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
            snapshot["warning"] = "Data is partial; some measures may be N/A."

        self.cache.set(normalized, snapshot)
        return snapshot


market_data_service = MarketDataService()
