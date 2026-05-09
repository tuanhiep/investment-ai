from collections.abc import AsyncIterator
from uuid import uuid4
import asyncio
import re
from typing import Any

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover - exercised when optional LLM dependency is absent.
    AsyncOpenAI = None  # type: ignore[assignment]

from backend.agents.investment_advisor_prompt import build_prompt
from backend.agents.graham_control import graham_qi_control
from backend.config.config import get_settings
from backend.schemas import ChatResponse, SourceDocument
from backend.services.knowledge_repository import KnowledgeChunk, load_knowledge, retrieve
from backend.services.market_data_service import market_data_service


TICKER_HINT_RE = re.compile(
    r"(?:ticker|stock|symbol|mã|ma|cổ phiếu|co phieu)\s+([A-Za-z][A-Za-z.\-]{0,7})",
    re.I,
)
STANDALONE_TICKER_RE = re.compile(r"\b[A-Z]{1,5}(?:\.[A-Z]{1,3})?\b")
TICKER_STOPWORDS = {
    "A",
    "AI",
    "AN",
    "AND",
    "API",
    "AS",
    "CEO",
    "CFO",
    "DCF",
    "EPS",
    "ETF",
    "FY",
    "GDP",
    "IPO",
    "LLM",
    "OF",
    "OR",
    "PE",
    "P/E",
    "ROE",
    "SEC",
    "THE",
    "TO",
    "USD",
    "VALUE",
}


class InvestmentAdvisor:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.knowledge = load_knowledge(self.settings.knowledge_file)
        if self.settings.openai_api_key and AsyncOpenAI is None:
            raise RuntimeError("OPENAI_API_KEY is set but the openai package is not installed.")
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None

    def _context(self, matches: list[tuple[KnowledgeChunk, float]]) -> str:
        if not matches:
            return "No internal knowledge matched the question."
        return "\n\n".join(
            "\n".join(
                [
                    f"Title: {chunk.title}",
                    f"Summary: {chunk.summary}",
                    f"Source: {chunk.source or 'Internal Graham knowledge base'}",
                    f"Source type: {chunk.source_type or 'curated note'}",
                    f"Quote: {chunk.quote or 'N/A'}",
                ]
            )
            for chunk, _score in matches
        )

    def _sources(self, matches: list[tuple[KnowledgeChunk, float]]) -> list[SourceDocument]:
        return [
            SourceDocument(
                title=chunk.title,
                summary=chunk.summary,
                quote=chunk.quote,
                source=chunk.source,
                source_type=chunk.source_type,
                score=score,
            )
            for chunk, score in matches
        ]

    def _extract_symbol(self, message: str) -> str | None:
        for candidate in STANDALONE_TICKER_RE.findall(message):
            normalized = candidate.strip(".-").upper()
            if normalized not in TICKER_STOPWORDS:
                return normalized

        hinted = TICKER_HINT_RE.search(message)
        if hinted:
            normalized = hinted.group(1).strip(".-").upper()
            if normalized not in TICKER_STOPWORDS:
                return normalized
        return None

    def _market_context(self, snapshot: dict[str, Any] | None, requested_symbol: str | None) -> str:
        if not requested_symbol:
            return "No ticker detected in the question."
        if not snapshot or snapshot.get("status") == "unavailable":
            return f"Ticker detected: {requested_symbol}. Current market data retrieval failed or returned unavailable."

        fields = [
            f"Symbol: {snapshot.get('symbol')}",
            f"Company: {snapshot.get('company_name') or 'N/A'}",
            f"Price: {snapshot.get('currency') or ''} {snapshot.get('price')}",
            f"As of: {snapshot.get('as_of') or 'N/A'}",
            f"P/E: {snapshot.get('pe')}",
            f"EPS: {snapshot.get('eps')}",
            f"ROE: {snapshot.get('roe')}",
            f"Revenue: {snapshot.get('revenue')}",
            f"Net income: {snapshot.get('net_income')}",
            f"Assets: {snapshot.get('assets')}",
            f"Liabilities: {snapshot.get('liabilities')}",
            f"Equity: {snapshot.get('equity')}",
            f"Current assets: {snapshot.get('current_assets')}",
            f"Current liabilities: {snapshot.get('current_liabilities')}",
            f"Cash and equivalents: {snapshot.get('cash_and_equivalents')}",
            f"Total debt: {snapshot.get('total_debt')}",
            f"Current ratio: {snapshot.get('current_ratio')}",
            f"Debt to equity: {snapshot.get('debt_to_equity')}",
            f"Working capital: {snapshot.get('working_capital')}",
            f"Operating cash flow: {snapshot.get('operating_cash_flow')}",
            f"Capital expenditures: {snapshot.get('capital_expenditures')}",
            f"Free cash flow: {snapshot.get('free_cash_flow')}",
            f"Annual history: {snapshot.get('annual_history')}",
            f"Positive earnings years: {snapshot.get('positive_earnings_years')} of {snapshot.get('earnings_years')}",
            f"Latest annual revenue: {snapshot.get('latest_annual_revenue')}",
            f"Oldest annual revenue: {snapshot.get('oldest_annual_revenue')}",
            f"Latest annual EPS: {snapshot.get('latest_annual_eps')}",
            f"Oldest annual EPS: {snapshot.get('oldest_annual_eps')}",
            f"Shares outstanding: {snapshot.get('shares_outstanding')}",
            f"Market cap: {snapshot.get('market_cap')}",
            f"Fiscal period: {snapshot.get('fiscal_period') or 'N/A'}",
            f"Source: {snapshot.get('source')}",
            f"Status: {snapshot.get('status')}",
            f"Warning: {snapshot.get('warning') or 'None'}",
        ]
        return "\n".join(fields)

    def _load_market_snapshot(self, message: str) -> tuple[str | None, dict[str, Any] | None]:
        symbol = self._extract_symbol(message)
        if not symbol:
            return None, None
        try:
            return symbol, market_data_service.get_stock_snapshot(symbol)
        except Exception:
            return symbol, None

    def _fallback_answer(
        self,
        question: str,
        matches: list[tuple[KnowledgeChunk, float]],
        market_snapshot: dict[str, Any] | None = None,
        requested_symbol: str | None = None,
    ) -> str:
        source = matches[0][0] if matches else None
        principle = source.title if source else "Margin of Safety"
        return graham_qi_control.assess(question, principle, market_snapshot, requested_symbol).to_markdown()

    async def ask(self, message: str, session_id: str | None = None) -> ChatResponse:
        matches = retrieve(message, self.knowledge)
        sources = self._sources(matches)
        session = session_id or str(uuid4())
        requested_symbol, market_snapshot = self._load_market_snapshot(message)

        if not self.client:
            return ChatResponse(
                session_id=session,
                answer=self._fallback_answer(message, matches, market_snapshot, requested_symbol),
                sources=sources,
                mode="local-fallback",
                market_snapshot=market_snapshot,
            )

        completion = await self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": "You speak in Benjamin Graham's disciplined investment voice."},
                {
                    "role": "user",
                    "content": build_prompt(
                        message,
                        self._context(matches),
                        self._market_context(market_snapshot, requested_symbol),
                    ),
                },
            ],
            temperature=0.25,
        )
        answer = completion.choices[0].message.content or ""
        return ChatResponse(
            session_id=session,
            answer=answer,
            sources=sources,
            mode="openai",
            market_snapshot=market_snapshot,
        )

    async def stream(self, message: str) -> AsyncIterator[str]:
        matches = retrieve(message, self.knowledge)
        requested_symbol, market_snapshot = self._load_market_snapshot(message)

        if not self.client:
            for token in self._fallback_answer(message, matches, market_snapshot, requested_symbol).split(" "):
                yield token + " "
                await asyncio.sleep(0.015)
            return

        stream = await self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": "You speak in Benjamin Graham's disciplined investment voice."},
                {
                    "role": "user",
                    "content": build_prompt(
                        message,
                        self._context(matches),
                        self._market_context(market_snapshot, requested_symbol),
                    ),
                },
            ],
            temperature=0.25,
            stream=True,
        )
        async for event in stream:
            token = event.choices[0].delta.content
            if token:
                yield token


advisor = InvestmentAdvisor()
