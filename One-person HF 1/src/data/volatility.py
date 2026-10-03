"""
Volatility calculations: historical vol, implied vol, IV rank, IV percentile,
volatility skew (25-delta risk reversal), and IV term structure.
Used by the /vol skill and Volatility-related agent queries.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import yfinance as yf
from scipy.stats import norm

DB_PATH = Path(__file__).parents[2] / "data" / "hedge_fund.db"


def historical_volatility(ticker: str, windows: list[int] = [20, 30, 60]) -> dict:
    t = yf.Ticker(ticker)
    hist = t.history(period="1y")
    if hist.empty:
        return {"error": f"No price data for {ticker}"}

    closes = hist["Close"]
    log_returns = np.log(closes / closes.shift(1)).dropna()

    result = {"ticker": ticker, "current_price": round(closes.iloc[-1], 2)}
    for w in windows:
        if len(log_returns) >= w:
            hv = log_returns.rolling(w).std().iloc[-1] * np.sqrt(252)
            result[f"hv_{w}d"] = round(float(hv) * 100, 2)
        else:
            result[f"hv_{w}d"] = None
    return result


def implied_volatility(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    expirations = t.options
    if not expirations:
        return {"error": f"No options data for {ticker}"}

    target = datetime.now() + timedelta(days=30)
    expiry = min(expirations, key=lambda d: abs((datetime.strptime(d, "%Y-%m-%d") - target).days))

    chain = t.option_chain(expiry)
    current_price = t.info.get("regularMarketPrice")
    if current_price is None:
        current_price = t.history(period="1d")["Close"].iloc[-1]

    calls = chain.calls.copy()
    puts = chain.puts.copy()
    calls["distance"] = abs(calls["strike"] - current_price)
    puts["distance"] = abs(puts["strike"] - current_price)

    atm_call_iv = calls.nsmallest(1, "distance").iloc[0]["impliedVolatility"]
    atm_put_iv = puts.nsmallest(1, "distance").iloc[0]["impliedVolatility"]
    atm_iv = (atm_call_iv + atm_put_iv) / 2

    return {
        "ticker": ticker,
        "expiry": expiry,
        "atm_iv": round(float(atm_iv) * 100, 2),
        "atm_call_iv": round(float(atm_call_iv) * 100, 2),
        "atm_put_iv": round(float(atm_put_iv) * 100, 2),
        "current_price": round(float(current_price), 2),
    }


def _bs_delta(S: float, K: float, T: float, sigma: float, r: float = 0.045, option_type: str = "call") -> float | None:
    """Black-Scholes delta. r defaults to approximate risk-free rate."""
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return None
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return float(norm.cdf(d1)) if option_type == "call" else float(norm.cdf(d1) - 1)


def volatility_skew(ticker: str) -> dict:
    """
    25-delta risk reversal and butterfly for the expiry closest to 30 days out.
    Risk reversal = 25d call IV - 25d put IV
      Positive: calls more expensive (upside skew / squeeze risk)
      Negative: puts more expensive (typical equity downside skew)
    Butterfly = (25d call IV + 25d put IV) / 2 - ATM IV
      Measures how fat the wings are relative to center.
    """
    t = yf.Ticker(ticker)
    expirations = t.options
    if not expirations:
        return {"error": f"No options data for {ticker}"}

    target = datetime.now() + timedelta(days=30)
    expiry = min(expirations, key=lambda d: abs((datetime.strptime(d, "%Y-%m-%d") - target).days))
    dte = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days
    T = max(dte / 365, 1 / 365)

    chain = t.option_chain(expiry)
    price = t.info.get("regularMarketPrice") or t.history(period="1d")["Close"].iloc[-1]

    calls = chain.calls[chain.calls["impliedVolatility"] > 0].copy()
    puts = chain.puts[chain.puts["impliedVolatility"] > 0].copy()

    # Compute BS delta for each strike
    calls["delta"] = calls.apply(
        lambda r: _bs_delta(price, r["strike"], T, r["impliedVolatility"], option_type="call"), axis=1
    )
    puts["delta"] = puts.apply(
        lambda r: _bs_delta(price, r["strike"], T, r["impliedVolatility"], option_type="put"), axis=1
    )

    calls = calls.dropna(subset=["delta"])
    puts = puts.dropna(subset=["delta"])

    # 25-delta call: call delta closest to 0.25
    if calls.empty or puts.empty:
        return {"error": "Insufficient options data for skew calculation"}

    calls["delta_dist"] = (calls["delta"] - 0.25).abs()
    puts["delta_dist"] = (puts["delta"] - (-0.25)).abs()

    atm_calls = calls.copy()
    atm_calls["atm_dist"] = (calls["strike"] - price).abs()
    atm_iv = atm_calls.nsmallest(1, "atm_dist").iloc[0]["impliedVolatility"]

    call_25d_row = calls.nsmallest(1, "delta_dist").iloc[0]
    put_25d_row = puts.nsmallest(1, "delta_dist").iloc[0]

    call_25d_iv = round(float(call_25d_row["impliedVolatility"]) * 100, 2)
    put_25d_iv = round(float(put_25d_row["impliedVolatility"]) * 100, 2)
    atm_iv_pct = round(float(atm_iv) * 100, 2)

    risk_reversal = round(call_25d_iv - put_25d_iv, 2)
    butterfly = round((call_25d_iv + put_25d_iv) / 2 - atm_iv_pct, 2)

    skew_interp = (
        "Calls expensive vs. puts — upside skew / potential squeeze risk"
        if risk_reversal > 1
        else "Puts expensive vs. calls — normal equity downside hedging"
        if risk_reversal < -1
        else "Skew balanced — no strong directional bias from options market"
    )

    return {
        "ticker": ticker,
        "expiry": expiry,
        "dte": dte,
        "atm_iv": atm_iv_pct,
        "call_25d_iv": call_25d_iv,
        "call_25d_strike": round(float(call_25d_row["strike"]), 2),
        "call_25d_delta": round(float(call_25d_row["delta"]), 3),
        "put_25d_iv": put_25d_iv,
        "put_25d_strike": round(float(put_25d_row["strike"]), 2),
        "put_25d_delta": round(float(put_25d_row["delta"]), 3),
        "risk_reversal_25d": risk_reversal,
        "butterfly_25d": butterfly,
        "skew_interpretation": skew_interp,
    }


def iv_term_structure(ticker: str) -> dict:
    """
    ATM IV across expiries closest to 7, 30, 60, and 90 days out.
    Identifies contango (normal) vs. backwardation (event risk priced in near-term).
    """
    t = yf.Ticker(ticker)
    expirations = t.options
    if not expirations:
        return {"error": f"No options data for {ticker}"}

    price = t.info.get("regularMarketPrice") or t.history(period="1d")["Close"].iloc[-1]
    targets = {"7d": 7, "30d": 30, "60d": 60, "90d": 90}
    result = {"ticker": ticker, "current_price": round(float(price), 2), "tenors": {}}

    for label, days in targets.items():
        target_date = datetime.now() + timedelta(days=days)
        expiry = min(expirations, key=lambda d: abs((datetime.strptime(d, "%Y-%m-%d") - target_date).days))
        dte = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days

        try:
            chain = t.option_chain(expiry)
            calls = chain.calls.copy()
            calls["dist"] = (calls["strike"] - price).abs()
            atm_call_iv = calls.nsmallest(1, "dist").iloc[0]["impliedVolatility"]

            puts = chain.puts.copy()
            puts["dist"] = (puts["strike"] - price).abs()
            atm_put_iv = puts.nsmallest(1, "dist").iloc[0]["impliedVolatility"]

            atm_iv = round((float(atm_call_iv) + float(atm_put_iv)) / 2 * 100, 2)
            result["tenors"][label] = {"expiry": expiry, "dte": dte, "atm_iv": atm_iv}
        except Exception:
            result["tenors"][label] = {"expiry": expiry, "dte": dte, "atm_iv": None}

    # Determine curve shape using 30d vs 90d
    iv_30 = result["tenors"].get("30d", {}).get("atm_iv")
    iv_90 = result["tenors"].get("90d", {}).get("atm_iv")
    iv_7 = result["tenors"].get("7d", {}).get("atm_iv")

    if iv_30 and iv_90:
        if iv_30 > iv_90 * 1.03:
            shape = "backwardation"
            shape_note = "Near-term IV elevated vs. back months — event risk or catalyst priced into front expiry"
        elif iv_90 > iv_30 * 1.03:
            shape = "contango"
            shape_note = "Normal contango — back months carry higher IV; front options relatively cheap"
        else:
            shape = "flat"
            shape_note = "Flat term structure — no strong near/far vol differential"
        result["curve_shape"] = shape
        result["curve_note"] = shape_note

    # Calendar spread signal
    if iv_7 and iv_30 and iv_7 > iv_30 * 1.10:
        result["calendar_signal"] = "Front week IV significantly elevated vs. 30-day — potential calendar spread: sell front, buy 30d"
    else:
        result["calendar_signal"] = None

    return result


def iv_rank_and_percentile(ticker: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT iv_30d_atm FROM iv_snapshots WHERE ticker = ? AND date >= ? ORDER BY date",
        (ticker, one_year_ago),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {"ticker": ticker, "iv_rank": None, "iv_percentile": None, "data_points": 0}

    historical_ivs = [r[0] for r in rows]
    current_iv_data = implied_volatility(ticker)
    if "error" in current_iv_data:
        return current_iv_data

    current_iv = current_iv_data["atm_iv"]
    iv_min = min(historical_ivs)
    iv_max = max(historical_ivs)

    iv_rank = round((current_iv - iv_min) / (iv_max - iv_min) * 100, 1) if iv_max != iv_min else 50.0
    iv_percentile = round(sum(1 for iv in historical_ivs if iv < current_iv) / len(historical_ivs) * 100, 1)

    return {
        "ticker": ticker,
        "current_iv": current_iv,
        "iv_rank": iv_rank,
        "iv_percentile": iv_percentile,
        "iv_52w_high": round(iv_max, 2),
        "iv_52w_low": round(iv_min, 2),
        "data_points": len(historical_ivs),
        "regime": _vol_regime(iv_rank),
    }


def store_iv_snapshot(ticker: str) -> dict:
    iv_data = implied_volatility(ticker)
    if "error" in iv_data:
        return iv_data

    hv_data = historical_volatility(ticker)

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT OR REPLACE INTO iv_snapshots (ticker, date, iv_30d_atm, hv_20d, hv_30d, hv_60d)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            ticker,
            datetime.now().strftime("%Y-%m-%d"),
            iv_data["atm_iv"],
            hv_data.get("hv_20d"),
            hv_data.get("hv_30d"),
            hv_data.get("hv_60d"),
        ),
    )
    conn.commit()
    conn.close()
    return {"stored": True, "ticker": ticker, "date": datetime.now().strftime("%Y-%m-%d")}


def full_vol_assessment(ticker: str) -> dict:
    hv = historical_volatility(ticker)
    iv = implied_volatility(ticker)

    if "error" in hv or "error" in iv:
        return {"error": hv.get("error") or iv.get("error")}

    iv_stats = iv_rank_and_percentile(ticker)
    skew = volatility_skew(ticker)
    term = iv_term_structure(ticker)
    store_iv_snapshot(ticker)

    hv_30d = hv.get("hv_30d", 0) or 0
    atm_iv = iv["atm_iv"]
    iv_premium = round(atm_iv - hv_30d, 2)

    return {
        "ticker": ticker,
        "current_price": hv["current_price"],
        "historical_vol": {
            "hv_20d": hv.get("hv_20d"),
            "hv_30d": hv.get("hv_30d"),
            "hv_60d": hv.get("hv_60d"),
        },
        "implied_vol": {
            "atm_iv": atm_iv,
            "expiry": iv["expiry"],
            "atm_call_iv": iv["atm_call_iv"],
            "atm_put_iv": iv["atm_put_iv"],
        },
        "iv_vs_hv": {
            "iv_premium_to_30d_hv": iv_premium,
            "interpretation": "Options expensive" if iv_premium > 5 else "Options cheap" if iv_premium < -5 else "Fairly priced",
        },
        "iv_rank": iv_stats.get("iv_rank"),
        "iv_percentile": iv_stats.get("iv_percentile"),
        "iv_52w_high": iv_stats.get("iv_52w_high"),
        "iv_52w_low": iv_stats.get("iv_52w_low"),
        "data_points": iv_stats.get("data_points", 0),
        "regime": iv_stats.get("regime", _vol_regime(iv_stats.get("iv_rank"))),
        "skew": skew if "error" not in skew else None,
        "term_structure": term if "error" not in term else None,
    }


def _vol_regime(iv_rank: float | None) -> str:
    if iv_rank is None:
        return "Unknown (insufficient history)"
    if iv_rank < 25:
        return "Low — options cheap, buyers favored"
    if iv_rank < 50:
        return "Normal"
    if iv_rank < 75:
        return "Elevated — sellers have edge"
    return "Extreme — options expensive"
