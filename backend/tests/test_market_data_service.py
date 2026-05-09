import unittest

from backend.services.market_data_service import CompanyFundamentals, MarketDataService, MarketPrice, TtlCache


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakePriceProvider:
    def __init__(self) -> None:
        self.calls = 0

    def get_price(self, symbol: str) -> MarketPrice:
        self.calls += 1
        return MarketPrice(
            symbol=symbol,
            price=100.0 + self.calls,
            open=99.0,
            high=102.0,
            low=98.0,
            volume=1_000,
            as_of="2026-05-09 16:00",
        )


class FakeFundamentalProvider:
    def __init__(self) -> None:
        self.calls = 0

    def get_fundamentals(self, symbol: str) -> CompanyFundamentals:
        self.calls += 1
        return CompanyFundamentals(
            symbol=symbol,
            cik="0000320193",
            company_name="Example Inc.",
            eps=5.0,
            roe=0.25,
            revenue=100_000_000.0,
            net_income=25_000_000.0,
            assets=200_000_000.0,
            liabilities=80_000_000.0,
            equity=120_000_000.0,
            shares_outstanding=10_000_000.0,
            fiscal_period="2026 FY",
            annual_history=[
                {"year": 2026, "revenue": 100_000_000.0, "net_income": 25_000_000.0, "eps": 5.0},
                {"year": 2025, "revenue": 90_000_000.0, "net_income": 20_000_000.0, "eps": 4.0},
            ],
            earnings_years=2,
            positive_earnings_years=2,
            latest_annual_revenue=100_000_000.0,
            oldest_annual_revenue=90_000_000.0,
            latest_annual_eps=5.0,
            oldest_annual_eps=4.0,
        )


class MarketDataServiceTest(unittest.TestCase):
    def test_stock_snapshot_combines_price_fundamentals_and_ratios(self) -> None:
        service = MarketDataService(
            price_provider=FakePriceProvider(),
            fundamental_provider=FakeFundamentalProvider(),
            cache=TtlCache(ttl_seconds=0),
        )

        snapshot = service.get_stock_snapshot("aapl")

        self.assertEqual(snapshot["symbol"], "AAPL")
        self.assertEqual(snapshot["status"], "available")
        self.assertEqual(snapshot["company_name"], "Example Inc.")
        self.assertAlmostEqual(snapshot["pe"], 20.2)
        self.assertEqual(snapshot["market_cap"], 1_010_000_000.0)
        self.assertEqual(snapshot["positive_earnings_years"], 2)
        self.assertEqual(len(snapshot["annual_history"]), 2)

    def test_stock_snapshot_uses_ttl_cache_until_expiry(self) -> None:
        clock = FakeClock()
        price_provider = FakePriceProvider()
        fundamental_provider = FakeFundamentalProvider()
        service = MarketDataService(
            price_provider=price_provider,
            fundamental_provider=fundamental_provider,
            cache=TtlCache(ttl_seconds=60, clock=clock),
        )

        first = service.get_stock_snapshot("MSFT")
        second = service.get_stock_snapshot("msft")

        self.assertEqual(first["cache_status"], "miss")
        self.assertEqual(second["cache_status"], "hit")
        self.assertEqual(price_provider.calls, 1)
        self.assertEqual(fundamental_provider.calls, 1)

        clock.advance(61)
        third = service.get_stock_snapshot("MSFT")

        self.assertEqual(third["cache_status"], "miss")
        self.assertEqual(price_provider.calls, 2)
        self.assertEqual(fundamental_provider.calls, 2)


if __name__ == "__main__":
    unittest.main()
