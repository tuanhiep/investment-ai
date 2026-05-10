import unittest

from backend.services.valuation_service import GrahamValuationService


class GrahamValuationServiceTest(unittest.TestCase):
    def test_analyze_computes_normalized_value_and_yields(self) -> None:
        service = GrahamValuationService()

        valuation = service.analyze(
            {
                "price": 100.0,
                "market_cap": 1_000_000_000.0,
                "shares_outstanding": 10_000_000.0,
                "current_assets": 500_000_000.0,
                "liabilities": 200_000_000.0,
                "eps": 5.0,
                "annual_history": [
                    {"year": 2025, "eps": 6.0, "free_cash_flow": 80_000_000.0},
                    {"year": 2024, "eps": 5.0, "free_cash_flow": 70_000_000.0},
                    {"year": 2023, "eps": 4.0, "free_cash_flow": 60_000_000.0},
                ],
            }
        )

        self.assertAlmostEqual(valuation.normalized_eps, 5.0)
        self.assertAlmostEqual(valuation.conservative_pe_value_per_share, 75.0)
        self.assertAlmostEqual(valuation.normalized_fcf, 70_000_000.0)
        self.assertAlmostEqual(valuation.fcf_yield, 0.07)
        self.assertAlmostEqual(valuation.net_current_asset_value, 300_000_000.0)
        self.assertAlmostEqual(valuation.net_current_asset_value_per_share, 30.0)


if __name__ == "__main__":
    unittest.main()
