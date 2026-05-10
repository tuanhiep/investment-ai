import asyncio
import unittest
from unittest.mock import patch

from backend.services.investment_advisor_service import InvestmentAdvisor


class FakeMarketDataService:
    def get_stock_snapshot(self, symbol: str) -> dict[str, object]:
        return {
            "symbol": symbol,
            "company_name": "Example Inc.",
            "price": 101.0,
            "pe": 20.2,
            "roe": 0.25,
            "eps": 5.0,
            "revenue": 100_000_000.0,
            "net_income": 25_000_000.0,
            "assets": 200_000_000.0,
            "liabilities": 80_000_000.0,
            "equity": 120_000_000.0,
            "shares_outstanding": 10_000_000.0,
            "market_cap": 1_010_000_000.0,
            "fiscal_period": "2026 FY",
            "as_of": "2026-05-09 16:00",
            "currency": "USD",
            "source": "Stooq + SEC EDGAR",
            "status": "available",
            "warning": None,
            "annual_history": [
                {"year": 2026, "revenue": 100_000_000.0, "net_income": 25_000_000.0, "eps": 5.0},
                {"year": 2025, "revenue": 90_000_000.0, "net_income": 20_000_000.0, "eps": 4.0},
            ],
            "earnings_years": 2,
            "positive_earnings_years": 2,
        }


class InvestmentAdvisorServiceTest(unittest.TestCase):
    def test_local_fallback_uses_current_market_snapshot_when_ticker_is_present(self) -> None:
        advisor = InvestmentAdvisor()
        advisor.client = None

        with patch("backend.services.investment_advisor_service.market_data_service", FakeMarketDataService()):
            response = asyncio.run(advisor.ask("AAPL có đủ biên an toàn không?"))

        self.assertEqual(response.mode, "local-fallback")
        self.assertIsNotNone(response.market_snapshot)
        self.assertEqual(response.market_snapshot["symbol"], "AAPL")
        self.assertIn("Evidence I can weigh", response.answer)
        self.assertIn("Margin of safety judgment", response.answer)
        self.assertTrue(response.sources)

    def test_ticker_extraction_ignores_financial_acronyms(self) -> None:
        advisor = InvestmentAdvisor()

        self.assertIsNone(advisor._extract_symbol("ROE và EPS có đủ tốt không?"))
        self.assertEqual(advisor._extract_symbol("cổ phiếu msft có hợp Graham không?"), "MSFT")
        self.assertEqual(advisor._extract_symbol("Should MSFT be examined as a growth stock or a value investment?"), "MSFT")
        self.assertIsNone(advisor._extract_symbol("Should this growth stock or value investment be examined?"))


if __name__ == "__main__":
    unittest.main()
