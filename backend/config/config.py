from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


class Settings:
    app_name = "InvestmentAI"
    api_prefix = "/api"
    cors_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    knowledge_file = Path(
        os.getenv("INVESTMENTAI_KNOWLEDGE_FILE", BASE_DIR / "db" / "data" / "graham_chunks.txt")
    )
    request_timeout = float(os.getenv("INVESTMENTAI_TIMEOUT_SECONDS", "30"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
