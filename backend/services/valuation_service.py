from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any


def _num(value: object) -> float | None:
    return value if isinstance(value, int | float) else None


def _safe_divide(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


@dataclass(frozen=True)
class ValuationSnapshot:
    normalized_eps: float | None
    normalized_fcf: float | None
    conservative_pe_value_per_share: float | None
    fcf_yield: float | None
    earnings_yield: float | None
    net_current_asset_value: float | None
    net_current_asset_value_per_share: float | None
    discount_to_conservative_value: float | None
    margin_of_safety_pct: float | None
    valuation_notes: list[str]


class GrahamValuationService:
    def analyze(self, market_snapshot: dict[str, Any]) -> ValuationSnapshot:
        annual_history = market_snapshot.get("annual_history") or []
        eps_values = [
            row["eps"]
            for row in annual_history
            if isinstance(row, dict) and isinstance(row.get("eps"), int | float) and row["eps"] > 0
        ]
        fcf_values = [
            row["free_cash_flow"]
            for row in annual_history
            if isinstance(row, dict)
            and isinstance(row.get("free_cash_flow"), int | float)
            and row["free_cash_flow"] > 0
        ]

        normalized_eps = mean(eps_values[:5]) if eps_values else _num(market_snapshot.get("eps"))
        normalized_fcf = mean(fcf_values[:5]) if fcf_values else _num(market_snapshot.get("free_cash_flow"))
        conservative_pe_value = normalized_eps * 15 if normalized_eps is not None else None

        price = _num(market_snapshot.get("price"))
        market_cap = _num(market_snapshot.get("market_cap"))
        shares = _num(market_snapshot.get("shares_outstanding"))
        current_assets = _num(market_snapshot.get("current_assets"))
        liabilities = _num(market_snapshot.get("liabilities"))
        net_current_asset_value = (
            current_assets - liabilities if current_assets is not None and liabilities is not None else None
        )
        ncav_per_share = _safe_divide(net_current_asset_value, shares)
        fcf_yield = _safe_divide(normalized_fcf, market_cap)
        earnings_yield = _safe_divide(_num(market_snapshot.get("eps")), price)
        discount_to_value = (
            _safe_divide(conservative_pe_value - price, conservative_pe_value)
            if conservative_pe_value is not None and price is not None
            else None
        )
        margin_of_safety_pct = discount_to_value if discount_to_value is not None and discount_to_value > 0 else 0.0

        notes = []
        if normalized_eps is None:
            notes.append("normalized EPS unavailable")
        if normalized_fcf is None:
            notes.append("normalized free cash flow unavailable")
        if conservative_pe_value is not None and price is not None and price > conservative_pe_value:
            notes.append("current price exceeds a conservative 15x normalized EPS appraisal")
        if ncav_per_share is not None and price is not None and price > ncav_per_share:
            notes.append("current price is not supported by net current asset value")
        if fcf_yield is not None and fcf_yield < 0.04:
            notes.append("normalized FCF yield is low for a defensive value purchase")

        return ValuationSnapshot(
            normalized_eps=normalized_eps,
            normalized_fcf=normalized_fcf,
            conservative_pe_value_per_share=conservative_pe_value,
            fcf_yield=fcf_yield,
            earnings_yield=earnings_yield,
            net_current_asset_value=net_current_asset_value,
            net_current_asset_value_per_share=ncav_per_share,
            discount_to_conservative_value=discount_to_value,
            margin_of_safety_pct=margin_of_safety_pct,
            valuation_notes=notes,
        )


graham_valuation_service = GrahamValuationService()
