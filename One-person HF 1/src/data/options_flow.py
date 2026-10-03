"""
Options flow analysis: OI distribution, put/call ratios, max pain, unusual activity.
Used by the /flow skill.
"""

from datetime import datetime, timedelta

import numpy as np
import yfinance as yf


def _get_price(ticker_obj) -> float:
    price = ticker_obj.info.get("regularMarketPrice")
    if price is None:
        price = ticker_obj.history(period="1d")["Close"].iloc[-1]
    return float(price)


def _nearest_expiry(expirations: list[str], days_out: int = 30) -> str:
    target = datetime.now() + timedelta(days=days_out)
    return min(expirations, key=lambda d: abs((datetime.strptime(d, "%Y-%m-%d") - target).days))


def put_call_ratios(ticker: str) -> dict:
    """Put/call ratios by volume and open interest across all near-term expiries."""
    t = yf.Ticker(ticker)
    expirations = t.options
    if not expirations:
        return {"error": f"No options data for {ticker}"}

    # Aggregate across first 4 expiries
    total_call_vol = total_put_vol = 0
    total_call_oi = total_put_oi = 0

    for expiry in expirations[:4]:
        try:
            chain = t.option_chain(expiry)
            total_call_vol += chain.calls["volume"].fillna(0).sum()
            total_put_vol += chain.puts["volume"].fillna(0).sum()
            total_call_oi += chain.calls["openInterest"].fillna(0).sum()
            total_put_oi += chain.puts["openInterest"].fillna(0).sum()
        except Exception:
            continue

    pc_vol = round(total_put_vol / total_call_vol, 3) if total_call_vol > 0 else None
    pc_oi = round(total_put_oi / total_call_oi, 3) if total_call_oi > 0 else None

    vol_sentiment = (
        "Bearish lean — elevated put buying"
        if pc_vol and pc_vol > 1.2
        else "Bullish lean — elevated call buying"
        if pc_vol and pc_vol < 0.7
        else "Neutral"
    )

    return {
        "ticker": ticker,
        "expiries_scanned": min(4, len(expirations)),
        "call_volume": int(total_call_vol),
        "put_volume": int(total_put_vol),
        "pc_volume_ratio": pc_vol,
        "call_oi": int(total_call_oi),
        "put_oi": int(total_put_oi),
        "pc_oi_ratio": pc_oi,
        "volume_sentiment": vol_sentiment,
    }


def max_pain(ticker: str, expiry: str | None = None) -> dict:
    """
    Max pain strike: the price at expiration where total option buyer value is minimized.
    Market makers are net short options and hedge toward this level into expiry.
    """
    t = yf.Ticker(ticker)
    expirations = t.options
    if not expirations:
        return {"error": f"No options data for {ticker}"}

    if expiry is None:
        expiry = _nearest_expiry(expirations, days_out=30)

    chain = t.option_chain(expiry)
    price = _get_price(t)

    calls = chain.calls[["strike", "openInterest"]].fillna(0)
    puts = chain.puts[["strike", "openInterest"]].fillna(0)

    all_strikes = sorted(set(calls["strike"].tolist() + puts["strike"].tolist()))

    pain = {}
    for test_price in all_strikes:
        call_value = sum(
            row["openInterest"] * max(0, test_price - row["strike"])
            for _, row in calls.iterrows()
        )
        put_value = sum(
            row["openInterest"] * max(0, row["strike"] - test_price)
            for _, row in puts.iterrows()
        )
        pain[test_price] = call_value + put_value

    mp_strike = min(pain, key=pain.get)
    distance_pct = round((mp_strike - price) / price * 100, 2)

    return {
        "ticker": ticker,
        "expiry": expiry,
        "current_price": round(price, 2),
        "max_pain_strike": mp_strike,
        "distance_from_price_pct": distance_pct,
        "interpretation": (
            f"Price needs to fall {abs(distance_pct):.1f}% to reach max pain"
            if distance_pct < 0
            else f"Price needs to rise {distance_pct:.1f}% to reach max pain"
            if distance_pct > 0
            else "Price is at max pain"
        ),
    }


def oi_distribution(ticker: str, expiry: str | None = None, top_n: int = 10) -> dict:
    """
    Top strikes by open interest for calls and puts.
    Identifies key resistance (call walls) and support (put walls).
    """
    t = yf.Ticker(ticker)
    expirations = t.options
    if not expirations:
        return {"error": f"No options data for {ticker}"}

    if expiry is None:
        expiry = _nearest_expiry(expirations, days_out=30)

    chain = t.option_chain(expiry)
    price = _get_price(t)

    calls = chain.calls[["strike", "openInterest", "impliedVolatility"]].fillna(0)
    puts = chain.puts[["strike", "openInterest", "impliedVolatility"]].fillna(0)

    top_calls = calls.nlargest(top_n, "openInterest")[["strike", "openInterest", "impliedVolatility"]].copy()
    top_puts = puts.nlargest(top_n, "openInterest")[["strike", "openInterest", "impliedVolatility"]].copy()

    top_calls["iv_pct"] = (top_calls["impliedVolatility"] * 100).round(1)
    top_puts["iv_pct"] = (top_puts["impliedVolatility"] * 100).round(1)

    # Identify call wall (highest OI call above current price) and put wall (highest OI put below)
    calls_above = calls[calls["strike"] > price]
    puts_below = puts[puts["strike"] < price]

    call_wall = calls_above.nlargest(1, "openInterest").iloc[0]["strike"] if not calls_above.empty else None
    put_wall = puts_below.nlargest(1, "openInterest").iloc[0]["strike"] if not puts_below.empty else None

    return {
        "ticker": ticker,
        "expiry": expiry,
        "current_price": round(price, 2),
        "call_wall": call_wall,
        "put_wall": put_wall,
        "top_calls": top_calls.to_dict("records"),
        "top_puts": top_puts.to_dict("records"),
    }


def unusual_options_activity(ticker: str, min_volume: int = 200, min_vol_oi_ratio: float = 2.5) -> dict:
    """
    Flags options with unusually high volume relative to open interest — a signal of
    fresh institutional or informed positioning rather than existing hedges rolling.
    Scans first 5 expiries.
    """
    t = yf.Ticker(ticker)
    expirations = t.options
    if not expirations:
        return {"error": f"No options data for {ticker}"}

    price = _get_price(t)
    unusual = []

    for expiry in expirations[:5]:
        dte = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days
        if dte < 2:
            continue
        try:
            chain = t.option_chain(expiry)
            for df, opt_type in [(chain.calls, "call"), (chain.puts, "put")]:
                df = df.copy()
                df = df[(df["volume"].fillna(0) >= min_volume) & (df["openInterest"].fillna(0) > 0)]
                df["vol_oi"] = df["volume"] / df["openInterest"]
                df = df[df["vol_oi"] >= min_vol_oi_ratio]

                for _, row in df.iterrows():
                    moneyness = round((row["strike"] - price) / price * 100, 1)
                    unusual.append({
                        "expiry": expiry,
                        "dte": dte,
                        "type": opt_type,
                        "strike": row["strike"],
                        "moneyness_pct": moneyness,
                        "volume": int(row["volume"]),
                        "open_interest": int(row["openInterest"]),
                        "vol_oi_ratio": round(float(row["vol_oi"]), 1),
                        "iv_pct": round(float(row["impliedVolatility"]) * 100, 1),
                        "last_price": round(float(row["lastPrice"]), 2),
                        "itm": (opt_type == "call" and row["strike"] < price)
                               or (opt_type == "put" and row["strike"] > price),
                    })
        except Exception:
            continue

    unusual.sort(key=lambda x: x["volume"], reverse=True)

    return {
        "ticker": ticker,
        "current_price": round(price, 2),
        "unusual_count": len(unusual),
        "unusual": unusual[:15],
    }


def full_flow_analysis(ticker: str) -> dict:
    """Orchestrates all flow analysis functions into a single result dict."""
    t = yf.Ticker(ticker)
    expirations = t.options
    if not expirations:
        return {"error": f"No options data for {ticker}"}

    # Use nearest 30-day expiry for OI and max pain
    expiry_30d = _nearest_expiry(expirations, days_out=30)

    return {
        "ticker": ticker,
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "put_call": put_call_ratios(ticker),
        "max_pain": max_pain(ticker, expiry=expiry_30d),
        "oi_distribution": oi_distribution(ticker, expiry=expiry_30d),
        "unusual_activity": unusual_options_activity(ticker),
    }
