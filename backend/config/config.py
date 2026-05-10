from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def _path_env(name: str, default: Path | None = None) -> Path | None:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    return Path(value)


class Settings:
    def __init__(self) -> None:
        self.app_name = "InvestmentAI"
        self.api_prefix = "/api"
        self.cors_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.sec_edgar_user_agent = os.getenv(
            "SEC_EDGAR_USER_AGENT",
            "InvestmentAI/1.0 contact@example.com",
        )
        self.market_data_timeout_seconds = float(os.getenv("MARKET_DATA_TIMEOUT_SECONDS", "8"))
        self.market_data_cache_ttl_seconds = float(os.getenv("MARKET_DATA_CACHE_TTL_SECONDS", "300"))
        self.use_mock_market_data = os.getenv("INVESTMENTAI_USE_MOCK_DATA", "false").lower() in ("1", "true", "yes")
        self.knowledge_file = _path_env("INVESTMENTAI_KNOWLEDGE_FILE", BASE_DIR / "db" / "data" / "graham_chunks.txt")
        self.system_prompt_file = _path_env("INVESTMENTAI_SYSTEM_PROMPT_FILE")
        self.request_timeout = float(os.getenv("INVESTMENTAI_TIMEOUT_SECONDS", "30"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
