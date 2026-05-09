from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def format_money(value: object) -> str:
    if not isinstance(value, int | float):
        return "N/A"
    abs_value = abs(value)
    if abs_value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"
    if abs_value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if abs_value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,.2f}"


def format_number(value: object, suffix: str = "") -> str:
    if not isinstance(value, int | float):
        return "N/A"
    return f"{value:.2f}{suffix}"


@dataclass(frozen=True)
class GrahamAssessment:
    direct_view: str
    evidence_lines: list[str]
    judgment: str
    missing_evidence: list[str]
    next_action: str

    def to_markdown(self) -> str:
        missing = ", ".join(self.missing_evidence) if self.missing_evidence else "nothing material in this snapshot"
        return (
            f"**Direct view:** {self.direct_view}\n\n"
            "**Evidence I can weigh:**\n"
            + "\n".join(self.evidence_lines)
            + "\n\n"
            f"**Margin of safety judgment:** {self.judgment}\n\n"
            f"**What remains outside this snapshot:** {missing}.\n\n"
            f"**Next action:** {self.next_action}"
        )


class GrahamQiControl:
    """Internal control plane: Qi terms map to engineering invariants, not factual evidence."""

    def assess(
        self,
        question: str,
        principle: str,
        market_snapshot: dict[str, Any] | None,
        requested_symbol: str | None,
    ) -> GrahamAssessment:
        if requested_symbol and (not market_snapshot or market_snapshot.get("status") == "unavailable"):
            return GrahamAssessment(
                direct_view=(
                    f"I cannot form a Graham judgment on `{requested_symbol}` because current market evidence "
                    "could not be retrieved. I will not replace current evidence with memory."
                ),
                evidence_lines=["- Current ticker-specific evidence is unavailable."],
                judgment=(
                    f"`{principle}` requires price, evidence, and conservative arithmetic. Reputation alone is not "
                    "an investment case."
                ),
                missing_evidence=["current price", "current financial statement evidence"],
                next_action="Retry the data pull, then examine price, earnings, assets, debt, liquidity, and cash generation.",
            )

        if not market_snapshot:
            return GrahamAssessment(
                direct_view=(
                    f"Without a ticker, I can only apply `{principle}`. I cannot judge a margin of safety without "
                    "a current price and business figures."
                ),
                evidence_lines=["- No ticker-specific evidence was supplied."],
                judgment="No conclusion. A security must be weighed against price, earnings, assets, and liabilities.",
                missing_evidence=["ticker", "current price", "financial statements"],
                next_action="Ask about a specific ticker or company, and I will weigh the available evidence first.",
            )

        context = _SnapshotContext(market_snapshot)
        valuation_flags = self._valuation_flags(context)
        strengths = self._strengths(context)
        missing_evidence = self._missing_evidence(context)

        direct_view = self._direct_view(question, context, valuation_flags)
        judgment = self._judgment(principle, strengths, valuation_flags)
        next_action = self._next_action(context, valuation_flags)

        return GrahamAssessment(
            direct_view=direct_view,
            evidence_lines=self._evidence_lines(context),
            judgment=judgment,
            missing_evidence=missing_evidence,
            next_action=next_action,
        )

    def _direct_view(self, question: str, context: "_SnapshotContext", valuation_flags: list[str]) -> str:
        question_lower = question.lower()
        if "growth stock" in question_lower and "value investment" in question_lower:
            return (
                f"For `{context.symbol}`, I would examine it first as a high-quality growth enterprise, then ask "
                "whether the offered price converts that quality into a value investment. On the present evidence, "
                "the business quality is more evident than the bargain."
            )
        if valuation_flags:
            return f"For `{context.symbol}`, I would not call this a Graham margin of safety at the present quotation."
        return (
            f"For `{context.symbol}`, the present figures do not disqualify the security, but they still do not prove "
            "a margin of safety."
        )

    def _valuation_flags(self, context: "_SnapshotContext") -> list[str]:
        flags: list[str] = []
        if isinstance(context.pe, int | float) and context.pe > 25:
            flags.append(f"the P/E of {format_number(context.pe)} is far above a defensive multiple")
        if isinstance(context.current_ratio, int | float) and context.current_ratio < 2:
            flags.append(f"the current ratio of {format_number(context.current_ratio)} is below a classic defensive threshold")
        if isinstance(context.debt_to_equity, int | float) and context.debt_to_equity > 1:
            flags.append(f"debt to equity of {format_number(context.debt_to_equity)} demands caution")
        if isinstance(context.net_current_asset_value, int | float) and isinstance(context.market_cap, int | float):
            if context.net_current_asset_value <= 0:
                flags.append("there is no net-current-asset bargain")
            elif context.market_cap > context.net_current_asset_value:
                flags.append("the market price is not below net current asset value")
        return flags

    def _strengths(self, context: "_SnapshotContext") -> list[str]:
        strengths: list[str] = []
        if isinstance(context.roe, int | float) and context.roe > 0.15:
            strengths.append(f"ROE is strong at {format_number(context.roe * 100, '%')}")
        if isinstance(context.free_cash_flow, int | float) and context.free_cash_flow > 0:
            strengths.append(f"free cash flow is positive at {format_money(context.free_cash_flow)}")
        if isinstance(context.working_capital, int | float) and context.working_capital > 0:
            strengths.append(f"working capital is positive at {format_money(context.working_capital)}")
        if (
            isinstance(context.positive_earnings_years, int)
            and isinstance(context.earnings_years, int)
            and context.earnings_years >= 5
        ):
            strengths.append(
                f"earnings were positive in {context.positive_earnings_years} of {context.earnings_years} annual filings"
            )
        return strengths

    def _judgment(self, principle: str, strengths: list[str], valuation_flags: list[str]) -> str:
        parts = [f"I am applying `{principle}`."]
        if strengths:
            parts.append("The favorable evidence is real: " + "; ".join(strengths) + ".")
        if valuation_flags:
            parts.append("The resistance comes from price and asset protection: " + "; ".join(valuation_flags) + ".")
        if not strengths and not valuation_flags:
            parts.append("The evidence is not yet sufficient to turn price into a defensible bargain.")
        parts.append(
            "A good business is not automatically a good purchase; the price paid is part of the proposition."
        )
        return " ".join(parts)

    def _missing_evidence(self, context: "_SnapshotContext") -> list[str]:
        missing = []
        if context.dividend_history is None:
            missing.append("dividend record")
        if context.industry_context is None:
            missing.append("industry cyclicality")
        if not isinstance(context.annual_history, list) or len(context.annual_history) < 5:
            missing.append("a full five-to-ten-year operating record")
        return missing

    def _next_action(self, context: "_SnapshotContext", valuation_flags: list[str]) -> str:
        if valuation_flags:
            return (
                "Treat the company as a watchlist candidate, not a bargain. Build a conservative intrinsic value "
                "range from normalized earnings and free cash flow, then require a substantial discount before acting."
            )
        return (
            "Build a conservative intrinsic value range from normalized earnings and free cash flow, then compare the "
            "current quote against that range before calling the security attractive."
        )

    def _evidence_lines(self, context: "_SnapshotContext") -> list[str]:
        lines = [
            f"- Company: {context.company}",
            f"- Price: {context.currency} {context.price} as of {context.as_of}",
            f"- P/E: {format_number(context.pe)}; EPS: {format_number(context.snapshot.get('eps'))}",
            f"- ROE: {format_number(context.roe * 100, '%') if isinstance(context.roe, int | float) else 'N/A'}",
            f"- Revenue: {format_money(context.snapshot.get('revenue'))}; net income: {format_money(context.snapshot.get('net_income'))}",
            f"- Assets: {format_money(context.snapshot.get('assets'))}; liabilities: {format_money(context.snapshot.get('liabilities'))}; equity: {format_money(context.snapshot.get('equity'))}",
            f"- Current ratio: {format_number(context.current_ratio)}; working capital: {format_money(context.working_capital)}",
            f"- Total debt: {format_money(context.snapshot.get('total_debt'))}; debt/equity: {format_number(context.debt_to_equity)}",
            f"- Operating cash flow: {format_money(context.snapshot.get('operating_cash_flow'))}; free cash flow: {format_money(context.free_cash_flow)}",
            f"- Annual earnings record: {context.positive_earnings_years or 'N/A'} positive years out of {context.earnings_years or 'N/A'} available annual filings",
            f"- Net current asset value estimate: {format_money(context.net_current_asset_value)}",
            f"- Source: {context.snapshot.get('source')} ({context.snapshot.get('fiscal_period') or 'latest available filing'})",
        ]
        annual_lines = []
        if isinstance(context.annual_history, list):
            for row in context.annual_history[:5]:
                if isinstance(row, dict):
                    annual_lines.append(
                        f"  - {row.get('year')}: revenue {format_money(row.get('revenue'))}, "
                        f"net income {format_money(row.get('net_income'))}, "
                        f"EPS {format_number(row.get('eps'))}, "
                        f"FCF {format_money(row.get('free_cash_flow'))}"
                    )
        if annual_lines:
            lines.append("- Recent annual record:\n" + "\n".join(annual_lines))
        return lines


@dataclass(frozen=True)
class _SnapshotContext:
    snapshot: dict[str, Any]

    @property
    def symbol(self) -> str:
        return str(self.snapshot.get("symbol") or "UNKNOWN")

    @property
    def company(self) -> str:
        return str(self.snapshot.get("company_name") or self.symbol)

    @property
    def currency(self) -> str:
        return str(self.snapshot.get("currency") or "")

    @property
    def price(self) -> Any:
        return self.snapshot.get("price")

    @property
    def as_of(self) -> str:
        return str(self.snapshot.get("as_of") or "N/A")

    @property
    def pe(self) -> Any:
        return self.snapshot.get("pe")

    @property
    def roe(self) -> Any:
        return self.snapshot.get("roe")

    @property
    def current_ratio(self) -> Any:
        return self.snapshot.get("current_ratio")

    @property
    def debt_to_equity(self) -> Any:
        return self.snapshot.get("debt_to_equity")

    @property
    def free_cash_flow(self) -> Any:
        return self.snapshot.get("free_cash_flow")

    @property
    def working_capital(self) -> Any:
        return self.snapshot.get("working_capital")

    @property
    def market_cap(self) -> Any:
        return self.snapshot.get("market_cap")

    @property
    def annual_history(self) -> Any:
        return self.snapshot.get("annual_history") or []

    @property
    def positive_earnings_years(self) -> Any:
        return self.snapshot.get("positive_earnings_years")

    @property
    def earnings_years(self) -> Any:
        return self.snapshot.get("earnings_years")

    @property
    def dividend_history(self) -> Any:
        return self.snapshot.get("dividend_history")

    @property
    def industry_context(self) -> Any:
        return self.snapshot.get("industry_context")

    @property
    def net_current_asset_value(self) -> float | None:
        current_assets = self.snapshot.get("current_assets")
        liabilities = self.snapshot.get("liabilities")
        if isinstance(current_assets, int | float) and isinstance(liabilities, int | float):
            return current_assets - liabilities
        return None


graham_qi_control = GrahamQiControl()
