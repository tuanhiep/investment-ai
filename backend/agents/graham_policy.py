from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from backend.services.valuation_service import ValuationSnapshot


class DecisionState(StrEnum):
    BARGAIN = "BARGAIN"
    WATCHLIST = "WATCHLIST"
    QUALITY_BUT_EXPENSIVE = "QUALITY_BUT_EXPENSIVE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    AVOID = "AVOID"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"


@dataclass(frozen=True)
class EvidenceScore:
    score: int
    strengths: list[str]
    gaps: list[str]


@dataclass(frozen=True)
class PolicyDecision:
    state: DecisionState
    evidence: EvidenceScore
    rationale: list[str]


class GrahamPolicyEngine:
    def decide(self, market_snapshot: dict[str, Any] | None, valuation: ValuationSnapshot | None) -> PolicyDecision:
        if not market_snapshot or market_snapshot.get("status") == "unavailable":
            return PolicyDecision(
                state=DecisionState.DATA_UNAVAILABLE,
                evidence=EvidenceScore(
                    score=0,
                    strengths=[],
                    gaps=["current market data", "current financial statement data"],
                ),
                rationale=["Current evidence is unavailable."],
            )

        evidence = self.score_evidence(market_snapshot)
        pe = _num(market_snapshot.get("pe"))
        current_ratio = _num(market_snapshot.get("current_ratio"))
        debt_to_equity = _num(market_snapshot.get("debt_to_equity"))
        positive_years = market_snapshot.get("positive_earnings_years")
        earnings_years = market_snapshot.get("earnings_years")
        fcf_yield = valuation.fcf_yield if valuation else None
        mos = valuation.margin_of_safety_pct if valuation else None
        ncav_per_share = valuation.net_current_asset_value_per_share if valuation else None
        price = _num(market_snapshot.get("price"))

        if evidence.score < 45:
            return PolicyDecision(
                state=DecisionState.INSUFFICIENT_EVIDENCE,
                evidence=evidence,
                rationale=["The evidence base is too thin for a Graham judgment."],
            )

        quality = (
            isinstance(positive_years, int)
            and isinstance(earnings_years, int)
            and earnings_years >= 5
            and positive_years == earnings_years
        )
        expensive = (pe is not None and pe > 25) or (fcf_yield is not None and fcf_yield < 0.04)
        weak_liquidity = current_ratio is not None and current_ratio < 1
        high_leverage = debt_to_equity is not None and debt_to_equity > 1.5

        if weak_liquidity or high_leverage:
            return PolicyDecision(
                state=DecisionState.AVOID,
                evidence=evidence,
                rationale=["Liquidity or leverage fails the defensive boundary."],
            )

        if (
            mos is not None
            and mos >= 0.30
            and current_ratio is not None
            and current_ratio >= 2
            and (debt_to_equity is None or debt_to_equity <= 1)
        ):
            return PolicyDecision(
                state=DecisionState.BARGAIN,
                evidence=evidence,
                rationale=["Price appears materially below a conservative appraisal with acceptable balance-sheet strength."],
            )

        if ncav_per_share is not None and price is not None and ncav_per_share > price:
            return PolicyDecision(
                state=DecisionState.BARGAIN,
                evidence=evidence,
                rationale=["Price is below estimated net current asset value."],
            )

        if quality and expensive:
            return PolicyDecision(
                state=DecisionState.QUALITY_BUT_EXPENSIVE,
                evidence=evidence,
                rationale=["Business quality is visible, but price does not offer a Graham discount."],
            )

        return PolicyDecision(
            state=DecisionState.WATCHLIST,
            evidence=evidence,
            rationale=["Evidence is usable, but the margin of safety has not been proven."],
        )

    def score_evidence(self, market_snapshot: dict[str, Any]) -> EvidenceScore:
        checks = [
            ("price", "current price"),
            ("eps", "earnings per share"),
            ("pe", "valuation multiple"),
            ("revenue", "revenue"),
            ("net_income", "net income"),
            ("assets", "assets"),
            ("liabilities", "liabilities"),
            ("equity", "equity"),
            ("current_assets", "current assets"),
            ("current_liabilities", "current liabilities"),
            ("operating_cash_flow", "operating cash flow"),
            ("free_cash_flow", "free cash flow"),
            ("annual_history", "annual history"),
        ]
        strengths = []
        gaps = []
        for key, label in checks:
            value = market_snapshot.get(key)
            if value not in (None, [], ""):
                strengths.append(label)
            else:
                gaps.append(label)

        score = round(len(strengths) / len(checks) * 100)
        if market_snapshot.get("status") == "partial":
            score = min(score, 70)
        return EvidenceScore(score=score, strengths=strengths, gaps=gaps)


def _num(value: object) -> float | None:
    return value if isinstance(value, int | float) else None


graham_policy_engine = GrahamPolicyEngine()
