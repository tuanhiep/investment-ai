import unittest

from backend.agents.graham_policy import DecisionState, GrahamPolicyEngine
from backend.services.valuation_service import GrahamValuationService


class GrahamPolicyEngineTest(unittest.TestCase):
    def test_quality_business_at_high_price_is_quality_but_expensive(self) -> None:
        snapshot = {
            "status": "available",
            "price": 415.12,
            "pe": 31.59,
            "eps": 13.14,
            "revenue": 241_832_000_000.0,
            "net_income": 97_983_000_000.0,
            "assets": 694_228_000_000.0,
            "liabilities": 279_861_000_000.0,
            "equity": 414_367_000_000.0,
            "current_assets": 175_329_000_000.0,
            "current_liabilities": 136_661_000_000.0,
            "current_ratio": 1.28,
            "operating_cash_flow": 127_494_000_000.0,
            "free_cash_flow": 47_348_000_000.0,
            "market_cap": 3_083_691_814_324.48,
            "positive_earnings_years": 5,
            "earnings_years": 5,
            "annual_history": [
                {"year": 2025, "eps": 9.68, "free_cash_flow": 59_475_000_000.0},
                {"year": 2024, "eps": 9.65, "free_cash_flow": 65_149_000_000.0},
                {"year": 2023, "eps": 8.05, "free_cash_flow": 56_118_000_000.0},
                {"year": 2022, "eps": 5.76, "free_cash_flow": 45_234_000_000.0},
                {"year": 2021, "eps": 5.06, "free_cash_flow": 38_260_000_000.0},
            ],
        }
        valuation = GrahamValuationService().analyze(snapshot)

        decision = GrahamPolicyEngine().decide(snapshot, valuation)

        self.assertEqual(decision.state, DecisionState.QUALITY_BUT_EXPENSIVE)
        self.assertGreaterEqual(decision.evidence.score, 90)

    def test_thin_data_is_insufficient_evidence(self) -> None:
        snapshot = {"status": "partial", "price": 10.0}
        valuation = GrahamValuationService().analyze(snapshot)

        decision = GrahamPolicyEngine().decide(snapshot, valuation)

        self.assertEqual(decision.state, DecisionState.INSUFFICIENT_EVIDENCE)
        self.assertLess(decision.evidence.score, 45)


if __name__ == "__main__":
    unittest.main()
