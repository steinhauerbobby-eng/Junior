"""
yfinance MCP server — exposes yfinance data as MCP tools.
Run as: python src/data/yfinance_client.py
"""

import json
import sys
from datetime import datetime, timedelta

import yfinance as yf


def get_price_history(ticker: str, period: str = "1y", interval: str = "1d") -> dict:
    t = yf.Ticker(ticker)
    hist = t.history(period=period, interval=interval)
    return {
        "ticker": ticker,
        "period": period,
        "interval": interval,
        "data": [
            {
                "date": str(idx.date()),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": row["Volume"],
            }
            for idx, row in hist.iterrows()
        ],
    }


def get_fundamentals(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    info = t.info
    keys = [
        "shortName", "sector", "industry", "marketCap", "enterpriseValue",
        "trailingPE", "forwardPE", "priceToBook", "priceToSalesTrailing12Months",
        "enterpriseToRevenue", "enterpriseToEbitda", "profitMargins", "grossMargins",
        "ebitdaMargins", "operatingMargins", "revenueGrowth", "earningsGrowth",
        "returnOnEquity", "returnOnAssets", "debtToEquity", "currentRatio",
        "totalRevenue", "ebitda", "freeCashflow", "totalDebt", "totalCash",
        "sharesOutstanding", "floatShares", "sharesShort", "shortRatio",
        "shortPercentOfFloat", "heldPercentInsiders", "heldPercentInstitutions",
        "beta", "52WeekChange", "fiftyTwoWeekHigh", "fiftyTwoWeekLow",
        "trailingEps", "forwardEps", "bookValue", "dividendYield",
    ]
    return {k: info.get(k) for k in keys}


def get_options_chain(ticker: str, expiry: str = None) -> dict:
    t = yf.Ticker(ticker)
    expirations = t.options
    if not expirations:
        return {"error": f"No options data available for {ticker}"}

    if expiry is None:
        # Pick expiry closest to 30 days out
        target = datetime.now() + timedelta(days=30)
        expiry = min(expirations, key=lambda d: abs((datetime.strptime(d, "%Y-%m-%d") - target).days))

    chain = t.option_chain(expiry)
    current_price = t.info.get("regularMarketPrice") or t.history(period="1d")["Close"].iloc[-1]

    # Find ATM options
    calls = chain.calls.copy()
    puts = chain.puts.copy()
    calls["distance"] = abs(calls["strike"] - current_price)
    puts["distance"] = abs(puts["strike"] - current_price)
    atm_call = calls.nsmallest(1, "distance").iloc[0]
    atm_put = puts.nsmallest(1, "distance").iloc[0]

    return {
        "ticker": ticker,
        "current_price": current_price,
        "expiry_used": expiry,
        "available_expiries": list(expirations),
        "atm_call": {
            "strike": atm_call["strike"],
            "impliedVolatility": atm_call["impliedVolatility"],
            "lastPrice": atm_call["lastPrice"],
            "openInterest": atm_call["openInterest"],
            "volume": atm_call["volume"],
        },
        "atm_put": {
            "strike": atm_put["strike"],
            "impliedVolatility": atm_put["impliedVolatility"],
            "lastPrice": atm_put["lastPrice"],
            "openInterest": atm_put["openInterest"],
            "volume": atm_put["volume"],
        },
        "atm_iv_avg": (atm_call["impliedVolatility"] + atm_put["impliedVolatility"]) / 2,
        "put_call_oi_ratio": puts["openInterest"].sum() / max(calls["openInterest"].sum(), 1),
    }


def get_macro_snapshot() -> dict:
    tickers = {
        "10Y_yield": "^TNX",
        "2Y_yield": "^IRX",
        "30Y_yield": "^TYX",
        "VIX": "^VIX",
        "VVIX": "^VVIX",
        "DXY": "DX-Y.NYB",
        "SP500": "^GSPC",
        "NDX": "^NDX",
        "Russell2000": "^RUT",
        "Gold": "GC=F",
        "WTI_crude": "CL=F",
        "Copper": "HG=F",
        "EUR_USD": "EURUSD=X",
        "USD_JPY": "JPY=X",
    }
    result = {}
    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="5d")
            if not hist.empty:
                current = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2] if len(hist) > 1 else current
                result[name] = {
                    "symbol": symbol,
                    "current": round(current, 4),
                    "change": round(current - prev, 4),
                    "change_pct": round((current - prev) / prev * 100, 2),
                }
        except Exception as e:
            result[name] = {"symbol": symbol, "error": str(e)}
    return result


def get_income_statement(ticker: str, quarterly: bool = False) -> dict:
    t = yf.Ticker(ticker)
    df = t.quarterly_income_stmt if quarterly else t.income_stmt
    return {"ticker": ticker, "quarterly": quarterly, "data": df.to_dict()}


def get_balance_sheet(ticker: str, quarterly: bool = False) -> dict:
    t = yf.Ticker(ticker)
    df = t.quarterly_balance_sheet if quarterly else t.balance_sheet
    return {"ticker": ticker, "quarterly": quarterly, "data": df.to_dict()}


def get_cash_flow(ticker: str, quarterly: bool = False) -> dict:
    t = yf.Ticker(ticker)
    df = t.quarterly_cashflow if quarterly else t.cashflow
    return {"ticker": ticker, "quarterly": quarterly, "data": df.to_dict()}


def get_insider_transactions(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    insiders = t.insider_transactions
    if insiders is None or insiders.empty:
        return {"ticker": ticker, "transactions": []}
    return {
        "ticker": ticker,
        "transactions": insiders.head(20).to_dict(orient="records"),
    }


def get_institutional_holders(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    inst = t.institutional_holders
    if inst is None or inst.empty:
        return {"ticker": ticker, "holders": []}
    return {
        "ticker": ticker,
        "holders": inst.to_dict(orient="records"),
    }


# MCP stdio interface
TOOLS = {
    "get_price_history": get_price_history,
    "get_fundamentals": get_fundamentals,
    "get_options_chain": get_options_chain,
    "get_macro_snapshot": get_macro_snapshot,
    "get_income_statement": get_income_statement,
    "get_balance_sheet": get_balance_sheet,
    "get_cash_flow": get_cash_flow,
    "get_insider_transactions": get_insider_transactions,
    "get_institutional_holders": get_institutional_holders,
}

if __name__ == "__main__":
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            tool = request.get("tool")
            params = request.get("params", {})
            if tool in TOOLS:
                result = TOOLS[tool](**params)
                print(json.dumps({"result": result}), flush=True)
            else:
                print(json.dumps({"error": f"Unknown tool: {tool}"}), flush=True)
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)
