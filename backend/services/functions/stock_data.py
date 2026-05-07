import yfinance as yf


def get_stock_data(symbol: str) -> dict:
    normalized = symbol.strip().upper()
    if not normalized:
        raise ValueError("Stock symbol is required")

    stock = yf.Ticker(symbol)
    info = stock.info
    return {
        "symbol": normalized,
        "pe": info.get("trailingPE"),
        "roe": info.get("returnOnEquity"),
        "eps": info.get("trailingEps"),
        "price": info.get("currentPrice"),
        "market_cap": info.get("marketCap"),
        "currency": info.get("currency"),
    }
