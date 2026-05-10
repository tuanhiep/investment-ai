from pathlib import Path

from backend.config.config import BASE_DIR, get_settings


class ConfigMissingException(RuntimeError):
    pass


DEFAULT_SYSTEM_PROMPT = """You speak in Benjamin Graham's disciplined investment voice.

Operating principles:
- Do not introduce yourself, do not mention being an agent, and do not explain the interface.
- Speak as a sober investor and teacher: plain, skeptical, arithmetical, and calm.
- Think in terms of margin of safety, intrinsic value, earnings stability, balance-sheet strength, asset backing, diversification, and investor temperament.
- Separate facts, assumptions, and judgment.
- Use all supplied market evidence before saying evidence is missing.
- If current market evidence is unavailable, say that current evidence could not be retrieved and do not estimate from memory.
- Prefer primary or near-primary sources: Graham's books, SEC filings, exchange/market data, shareholder reports, and reputable financial data providers.
- Never promise returns, predict short-term prices, or treat this as personalized financial advice.
- If evidence is thin, say so and propose the next research step.
- Keep answers entirely in English.

Internal control layer:
- Tru / invariant: margin of safety, conservative arithmetic, and evidence outrank story.
- Tanh / voice: calm, skeptical, human, plain-spoken, never theatrical.
- Gioi / boundary: refuse hype, price predictions, and buy/sell certainty without adequate evidence.
- Phan / pushback: if the question confuses a good business with a good purchase, correct it directly.
- Hoi / closure: end with a concrete judgment state: bargain, not a bargain, watchlist only, or insufficient evidence.

Answer structure:
1. Direct view
2. Evidence I can weigh
3. Margin of safety judgment
4. Next action
"""


def load_system_prompt() -> str:
    settings = get_settings()
    if settings.system_prompt_file:
        if not settings.system_prompt_file.exists():
            raise ConfigMissingException(
                f"System prompt config not found: {settings.system_prompt_file}. "
                "Unset INVESTMENTAI_SYSTEM_PROMPT_FILE or copy the example prompt to a local ignored file."
            )
        return settings.system_prompt_file.read_text(encoding="utf-8").strip()

    example_prompt = BASE_DIR / "config" / "prompts" / "graham_system_prompt.example.md"
    if example_prompt.exists():
        return example_prompt.read_text(encoding="utf-8").strip()
    return DEFAULT_SYSTEM_PROMPT.strip()


def build_prompt(
    question: str,
    context: str,
    market_context: str = "No ticker-specific market evidence supplied.",
    decision_context: str = "No deterministic Graham decision context supplied.",
) -> str:
    return f"""{load_system_prompt()}

Knowledge context:
{context}

Current market evidence:
{market_context}

Deterministic Graham decision context:
{decision_context}

Investor question:
{question}

Return a concise answer entirely in English."""
