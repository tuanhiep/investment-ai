import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from backend.agents.investment_advisor_prompt import ConfigMissingException, load_system_prompt
from backend.config.config import get_settings
from backend.services.market_data_service import MarketDataService, MockFundamentalProvider, MockPriceProvider


class PublicConfigurationTest(unittest.TestCase):
    def tearDown(self) -> None:
        get_settings.cache_clear()

    def test_default_prompt_loads_from_public_example(self) -> None:
        with patch.dict(os.environ, {"INVESTMENTAI_SYSTEM_PROMPT_FILE": ""}, clear=False):
            get_settings.cache_clear()

            prompt = load_system_prompt()

        self.assertIn("Benjamin Graham", prompt)
        self.assertIn("Tru / invariant", prompt)

    def test_missing_private_prompt_path_fails_loudly(self) -> None:
        with TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "graham_system_prompt.local.md"
            with patch.dict(os.environ, {"INVESTMENTAI_SYSTEM_PROMPT_FILE": str(missing)}, clear=False):
                get_settings.cache_clear()

                with self.assertRaises(ConfigMissingException):
                    load_system_prompt()

    def test_mock_market_data_mode_runs_without_network_clients(self) -> None:
        with patch.dict(os.environ, {"INVESTMENTAI_USE_MOCK_DATA": "true"}, clear=False):
            get_settings.cache_clear()
            service = MarketDataService()

        snapshot = service.get_stock_snapshot("MSFT")

        self.assertIsInstance(service.price_provider, MockPriceProvider)
        self.assertIsInstance(service.fundamental_provider, MockFundamentalProvider)
        self.assertEqual(snapshot["symbol"], "MSFT")
        self.assertEqual(snapshot["status"], "available")
        self.assertEqual(snapshot["positive_earnings_years"], 5)


if __name__ == "__main__":
    unittest.main()
