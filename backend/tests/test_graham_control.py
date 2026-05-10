import unittest

from backend.agents.graham_control import GrahamQiControl


class GrahamQiControlTest(unittest.TestCase):
    def test_growth_vs_value_question_gets_human_graham_pushback(self) -> None:
        control = GrahamQiControl()
        assessment = control.assess(
            question="Should MSFT be examined as a growth stock or a value investment?",
            principle="Growth Stock Discipline",
            requested_symbol="MSFT",
            market_snapshot={
                "symbol": "MSFT",
                "company_name": "MICROSOFT CORPORATION",
                "price": 415.12,
                "as_of": "2026-05-08 22:00:21",
                "currency": "USD",
                "pe": 31.59,
                "eps": 13.14,
                "roe": 0.236,
                "revenue": 241_832_000_000.0,
                "net_income": 97_983_000_000.0,
                "assets": 694_228_000_000.0,
                "liabilities": 279_861_000_000.0,
                "equity": 414_367_000_000.0,
                "current_assets": 175_329_000_000.0,
                "current_liabilities": 136_661_000_000.0,
                "current_ratio": 1.28,
                "total_debt": 49_101_000_000.0,
                "debt_to_equity": 0.12,
                "working_capital": 38_668_000_000.0,
                "operating_cash_flow": 127_494_000_000.0,
                "free_cash_flow": 47_348_000_000.0,
                "market_cap": 3_083_691_814_324.48,
                "positive_earnings_years": 10,
                "earnings_years": 10,
                "annual_history": [
                    {"year": 2025, "revenue": 211_915_000_000.0, "net_income": 72_361_000_000.0, "eps": 9.68},
                    {"year": 2024, "revenue": 198_270_000_000.0, "net_income": 72_738_000_000.0, "eps": 9.65},
                    {"year": 2023, "revenue": 168_088_000_000.0, "net_income": 61_271_000_000.0, "eps": 8.05},
                    {"year": 2022, "revenue": 143_015_000_000.0, "net_income": 44_281_000_000.0, "eps": 5.76},
                    {"year": 2021, "revenue": 125_843_000_000.0, "net_income": 39_240_000_000.0, "eps": 5.06},
                ],
                "source": "Stooq + SEC EDGAR",
                "fiscal_period": "2026 Q3",
            },
        )

        rendered = assessment.to_markdown()

        self.assertIn("high-quality growth enterprise", assessment.direct_view)
        self.assertIn("the business quality is more evident than the bargain", assessment.direct_view)
        self.assertIn("A good business is not automatically a good purchase", rendered)
        self.assertIn("watchlist candidate", rendered)
        self.assertEqual(assessment.decision_state, "QUALITY_BUT_EXPENSIVE")
        self.assertGreaterEqual(assessment.evidence_score, 90)

    def test_unavailable_market_data_refuses_memory_substitution(self) -> None:
        control = GrahamQiControl()
        assessment = control.assess(
            question="Does XYZ offer a margin of safety?",
            principle="Margin of Safety",
            requested_symbol="XYZ",
            market_snapshot={"symbol": "XYZ", "status": "unavailable"},
        )

        self.assertIn("could not be retrieved", assessment.direct_view)
        self.assertIn("will not replace current evidence with memory", assessment.direct_view)
        self.assertEqual(assessment.decision_state, "DATA_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
