import yfinance as yf

def get_stock_data(symbol):
    stock = yf.Ticker(symbol)
    info = stock.info
    return {
        "symbol": symbol,
        "pe": info.get("trailingPE"),
        "roe": info.get("returnOnEquity"),
        "eps": info.get("trailingEps"),
        "price": info.get("currentPrice"),
    }
