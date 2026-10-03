"""
Liquidity analysis module.
- Fetches FRED series via requests (requires network access; gracefully degrades)
- Fetches market proxy data via yfinance (always works)
- Computes Net Fed Liquidity, global liquidity impulse, and liquidity score
- FRED key optional: set FRED_API_KEY env var; falls back to public CSV endpoint
"""

import os
import io
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# FRED series IDs and metadata
FRED_SERIES = {
    "WALCL":     {"label": "Fed Balance Sheet",        "unit": "B",  "freq": "W"},
    "WTREGEN":   {"label": "Treasury General Account", "unit": "M→B","freq": "W"},  # reported in millions
    "RRPONTSYD": {"label": "Reverse Repo (RRP)",        "unit": "B",  "freq": "D"},
    "WRESBAL":   {"label": "Bank Reserves",             "unit": "B",  "freq": "W"},
    "M2SL":      {"label": "M2 Money Supply",           "unit": "B",  "freq": "M"},
    "TOTLL":     {"label": "Total Loans & Leases",      "unit": "B",  "freq": "W"},
    "CPIAUCSL":  {"label": "CPI (for real M2)",         "unit": "idx","freq": "M"},
}

# Net liquidity formula: Fed BS - TGA - RRP
# When TGA rises → drains reserves (restrictive) → subtract
# When RRP rises → absorbs reserves (restrictive) → subtract
# When Fed BS rises → adds reserves (stimulative) → add


def _fetch_fred_csv(series_id: str, limit_rows: int = 104) -> pd.DataFrame | None:
    """
    Fetch a FRED series via the public CSV download endpoint (no API key required).
    Returns a DataFrame with columns [date, value] sorted ascending, or None on failure.
    """
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; research/1.0)"}
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code != 200:
            return None
        df = pd.read_csv(io.StringIO(r.text), parse_dates=[0])
        df.columns = ["date", "value"]
        df = df[df["value"] != "."].dropna()
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna().sort_values("date").tail(limit_rows).reset_index(drop=True)
        return df
    except Exception:
        return None


def _fetch_fred_api(series_id: str, limit: int = 104) -> pd.DataFrame | None:
    """Fetch via FRED API (requires FRED_API_KEY)."""
    if not FRED_API_KEY:
        return None
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return None
        obs = r.json().get("observations", [])
        rows = [(o["date"], o["value"]) for o in obs if o["value"] != "."]
        df = pd.DataFrame(rows, columns=["date", "value"])
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna().sort_values("date").reset_index(drop=True)
        return df
    except Exception:
        return None


def fetch_fred(series_id: str) -> pd.DataFrame | None:
    """Try API first (fast), fall back to CSV."""
    return _fetch_fred_api(series_id) or _fetch_fred_csv(series_id)


def get_market_proxies() -> dict:
    """
    Pull market-based liquidity proxies via yfinance.
    These are always available regardless of FRED network access.
    """
    tickers = {
        "DXY":     "DX-Y.NYB",   # Dollar index — inverse global liquidity
        "Gold":    "GC=F",        # Real store of value / liquidity hedge
        "Copper":  "HG=F",        # Industrial demand / global growth proxy
        "BTC":     "BTC-USD",     # Risk / liquidity barometer (crypto)
        "SPX":     "^GSPC",       # US equity
        "HYG":     "HYG",         # High yield credit (risk appetite)
        "LQD":     "LQD",         # Investment grade credit
        "EEM":     "EEM",         # EM equities (dollar-sensitive)
        "10Y":     "^TNX",        # 10-year Treasury yield
        "2Y":      "^IRX",        # 2-year yield
        "VIX":     "^VIX",        # Volatility / risk-off
    }
    result = {}
    end = datetime.now()
    start_4w = end - timedelta(days=30)
    start_13w = end - timedelta(days=91)
    start_1y = end - timedelta(days=365)

    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="1y")
            if hist.empty:
                continue
            price_now = hist["Close"].iloc[-1]
            price_4w = hist["Close"][hist.index >= pd.Timestamp(start_4w, tz=hist.index.tz)].iloc[0] if len(hist[hist.index >= pd.Timestamp(start_4w, tz=hist.index.tz)]) else hist["Close"].iloc[-22]
            price_13w = hist["Close"][hist.index >= pd.Timestamp(start_13w, tz=hist.index.tz)].iloc[0] if len(hist[hist.index >= pd.Timestamp(start_13w, tz=hist.index.tz)]) else hist["Close"].iloc[-65]
            price_1y = hist["Close"].iloc[0]

            result[name] = {
                "symbol": symbol,
                "price": round(price_now, 4),
                "chg_4w_pct": round((price_now - price_4w) / price_4w * 100, 2),
                "chg_13w_pct": round((price_now - price_13w) / price_13w * 100, 2),
                "chg_1y_pct": round((price_now - price_1y) / price_1y * 100, 2),
            }
        except Exception as e:
            result[name] = {"symbol": symbol, "error": str(e)}
    return result


def get_fred_liquidity_data() -> dict:
    """
    Fetch all FRED liquidity series and compute derived metrics.
    Returns dict with each series' current level, 4w change, 13w change, and YoY change.
    Returns None values for series that couldn't be fetched.
    """
    out = {}

    for sid, meta in FRED_SERIES.items():
        df = fetch_fred(sid)
        if df is None or df.empty:
            out[sid] = {"label": meta["label"], "available": False, "latest": None}
            continue

        # Convert TGA from millions to billions
        if meta["unit"] == "M→B":
            df["value"] = df["value"] / 1000

        latest = df.iloc[-1]
        latest_val = latest["value"]
        latest_date = latest["date"]

        # 4-week lookback
        cutoff_4w = latest_date - pd.Timedelta(weeks=4)
        df_4w = df[df["date"] <= cutoff_4w]
        val_4w = df_4w.iloc[-1]["value"] if not df_4w.empty else None

        # 13-week lookback
        cutoff_13w = latest_date - pd.Timedelta(weeks=13)
        df_13w = df[df["date"] <= cutoff_13w]
        val_13w = df_13w.iloc[-1]["value"] if not df_13w.empty else None

        # 52-week lookback (YoY)
        cutoff_1y = latest_date - pd.Timedelta(weeks=52)
        df_1y = df[df["date"] <= cutoff_1y]
        val_1y = df_1y.iloc[-1]["value"] if not df_1y.empty else None

        out[sid] = {
            "label": meta["label"],
            "unit": "B (USD)",
            "available": True,
            "latest_date": str(latest_date.date()),
            "latest": round(latest_val, 1),
            "val_4w_ago": round(val_4w, 1) if val_4w else None,
            "val_13w_ago": round(val_13w, 1) if val_13w else None,
            "val_1y_ago": round(val_1y, 1) if val_1y else None,
            "chg_4w": round(latest_val - val_4w, 1) if val_4w else None,
            "chg_13w": round(latest_val - val_13w, 1) if val_13w else None,
            "chg_1y": round(latest_val - val_1y, 1) if val_1y else None,
            "chg_yoy_pct": round((latest_val - val_1y) / val_1y * 100, 1) if val_1y else None,
        }

    return out


def compute_net_fed_liquidity(fred_data: dict) -> dict:
    """
    Net Fed Liquidity = Fed BS - TGA - RRP
    When positive change → easing; when negative → tightening.
    """
    def get_val(sid, key):
        d = fred_data.get(sid, {})
        return d.get(key) if d.get("available") else None

    fed_bs = get_val("WALCL", "latest")
    tga = get_val("WTREGEN", "latest")
    rrp = get_val("RRPONTSYD", "latest")

    fed_bs_4w = get_val("WALCL", "val_4w_ago")
    tga_4w = get_val("WTREGEN", "val_4w_ago")
    rrp_4w = get_val("RRPONTSYD", "val_4w_ago")

    fed_bs_13w = get_val("WALCL", "val_13w_ago")
    tga_13w = get_val("WTREGEN", "val_13w_ago")
    rrp_13w = get_val("RRPONTSYD", "val_13w_ago")

    def nfl(bs, tga_, rrp_):
        if any(x is None for x in [bs, tga_, rrp_]):
            return None
        return round(bs - tga_ - rrp_, 1)

    nfl_now = nfl(fed_bs, tga, rrp)
    nfl_4w = nfl(fed_bs_4w, tga_4w, rrp_4w)
    nfl_13w = nfl(fed_bs_13w, tga_13w, rrp_13w)

    return {
        "nfl_current": nfl_now,
        "nfl_4w_ago": nfl_4w,
        "nfl_13w_ago": nfl_13w,
        "impulse_4w": round(nfl_now - nfl_4w, 1) if (nfl_now and nfl_4w) else None,
        "impulse_13w": round(nfl_now - nfl_13w, 1) if (nfl_now and nfl_13w) else None,
        "components": {
            "fed_bs": fed_bs,
            "tga": tga,
            "rrp": rrp,
            "fed_bs_chg_4w": round(fed_bs - fed_bs_4w, 1) if (fed_bs and fed_bs_4w) else None,
            "tga_chg_4w": round(tga - tga_4w, 1) if (tga and tga_4w) else None,
            "rrp_chg_4w": round(rrp - rrp_4w, 1) if (rrp and rrp_4w) else None,
        },
    }


def compute_liquidity_score(fred_data: dict, market_proxies: dict) -> dict:
    """
    Liquidity score: -10 (maximum tightening) to +10 (maximum easing).
    8 components, each scored -2 to +2, then summed and rounded to 1 decimal.

    Thresholds:
    Component 1 — Fed BS 4w change ($B):  <-50=-2, -50:-10=-1, ±10=0, 10:50=+1, >50=+2
    Component 2 — TGA 4w change (inverted): >+100=-2, 50:100=-1, ±50=0, -100:-50=+1, <-100=+2
    Component 3 — RRP 4w change (inverted): >+100=-2, 50:100=-1, ±50=0, -100:-50=+1, <-100=+2
    Component 4 — Bank Reserves level ($B): <2000=-2, 2000:2500=-1, 2500:3000=0, 3000:3500=+1, >3500=+2
    Component 5 — M2 YoY growth (%):       <-2=-2, -2:0=-1, 0:4=0, 4:8=+1, >8=+2
    Component 6 — DXY 4w change (inv, %):  >+3=-2, 1:3=-1, ±1=0, -3:-1=+1, <-3=+2
    Component 7 — Credit (Loans) YoY (%):  <0=-2, 0:3=-1, 3:6=0, 6:10=+1, >10=+2
    Component 8 — Net Fed Liquidity impulse 4w ($B): <-100=-2, -100:-25=-1, ±25=0, 25:100=+1, >100=+2
    """
    scores = {}

    def val(sid, key):
        d = fred_data.get(sid, {})
        return d.get(key) if d.get("available") else None

    def score_thresholds(value, breakpoints, points):
        """breakpoints: ascending list of thresholds; points: list of scores (len = len(breakpoints)+1)"""
        if value is None:
            return 0  # neutral if data unavailable
        for i, bp in enumerate(breakpoints):
            if value < bp:
                return points[i]
        return points[-1]

    # C1: Fed BS 4w change
    fed_bs_chg = val("WALCL", "chg_4w")
    c1 = score_thresholds(fed_bs_chg, [-50, -10, 10, 50], [-2, -1, 0, 1, 2])
    scores["fed_bs_4w"] = {"label": "Fed BS 4w change", "value": fed_bs_chg, "score": c1, "unit": "$B"}

    # C2: TGA 4w change (inverted — TGA rise is restrictive)
    tga_chg = val("WTREGEN", "chg_4w")
    tga_inv = -tga_chg if tga_chg is not None else None
    c2 = score_thresholds(tga_inv, [-100, -50, 50, 100], [-2, -1, 0, 1, 2])
    scores["tga_4w"] = {"label": "TGA 4w change (inv.)", "value": tga_chg, "score": c2, "unit": "$B"}

    # C3: RRP 4w change (inverted — RRP rise is restrictive)
    rrp_chg = val("RRPONTSYD", "chg_4w")
    rrp_inv = -rrp_chg if rrp_chg is not None else None
    c3 = score_thresholds(rrp_inv, [-100, -50, 50, 100], [-2, -1, 0, 1, 2])
    scores["rrp_4w"] = {"label": "RRP 4w change (inv.)", "value": rrp_chg, "score": c3, "unit": "$B"}

    # C4: Bank reserves level
    reserves = val("WRESBAL", "latest")
    c4 = score_thresholds(reserves, [2000, 2500, 3000, 3500], [-2, -1, 0, 1, 2])
    scores["bank_reserves"] = {"label": "Bank reserves level", "value": reserves, "score": c4, "unit": "$B"}

    # C5: M2 YoY growth
    m2_yoy = val("M2SL", "chg_yoy_pct")
    c5 = score_thresholds(m2_yoy, [-2, 0, 4, 8], [-2, -1, 0, 1, 2])
    scores["m2_yoy"] = {"label": "M2 YoY growth", "value": m2_yoy, "score": c5, "unit": "%"}

    # C6: DXY 4w change (inverted — stronger dollar = tighter global liquidity)
    dxy = market_proxies.get("DXY", {})
    dxy_chg = dxy.get("chg_4w_pct")
    dxy_inv = -dxy_chg if dxy_chg is not None else None
    c6 = score_thresholds(dxy_inv, [-3, -1, 1, 3], [-2, -1, 0, 1, 2])
    scores["dxy_4w"] = {"label": "DXY 4w change (inv.)", "value": dxy_chg, "score": c6, "unit": "%"}

    # C7: Credit growth (total loans YoY)
    loans_yoy = val("TOTLL", "chg_yoy_pct")
    c7 = score_thresholds(loans_yoy, [0, 3, 6, 10], [-2, -1, 0, 1, 2])
    scores["credit_growth"] = {"label": "Credit (loans) YoY", "value": loans_yoy, "score": c7, "unit": "%"}

    # C8: Net Fed Liquidity impulse 4w
    nfl_impulse = None
    nfl_data = compute_net_fed_liquidity(fred_data)
    nfl_impulse = nfl_data.get("impulse_4w")
    c8 = score_thresholds(nfl_impulse, [-100, -25, 25, 100], [-2, -1, 0, 1, 2])
    scores["nfl_impulse"] = {"label": "Net Fed Liquidity impulse 4w", "value": nfl_impulse, "score": c8, "unit": "$B"}

    total = sum(s["score"] for s in scores.values())

    if total >= 6:
        regime = "STRONG EASING"
        asset_implication = "Significant risk asset tailwind — liquidity is expanding materially"
    elif total >= 2:
        regime = "MODERATE EASING"
        asset_implication = "Mild liquidity tailwind — supportive but not a strong mechanical driver"
    elif total >= -1:
        regime = "NEUTRAL"
        asset_implication = "Liquidity neither a headwind nor tailwind — fundamentals and earnings drive prices"
    elif total >= -5:
        regime = "MODERATE TIGHTENING"
        asset_implication = "Mild liquidity headwind — risk assets face moderate mechanical pressure"
    else:
        regime = "STRONG TIGHTENING"
        asset_implication = "Significant risk asset headwind — liquidity contraction is a primary driver"

    return {
        "total_score": round(total, 1),
        "regime": regime,
        "asset_implication": asset_implication,
        "components": scores,
    }


def run_full_liquidity_assessment() -> dict:
    """Master function: pull all data, compute metrics, return complete assessment."""
    print("Fetching market proxies (yfinance)...")
    market_proxies = get_market_proxies()

    print("Fetching FRED liquidity series...")
    fred_data = get_fred_liquidity_data()

    print("Computing Net Fed Liquidity...")
    nfl = compute_net_fed_liquidity(fred_data)

    print("Computing liquidity score...")
    score = compute_liquidity_score(fred_data, market_proxies)

    return {
        "as_of": datetime.now().strftime("%Y-%m-%d"),
        "market_proxies": market_proxies,
        "fred_data": fred_data,
        "net_fed_liquidity": nfl,
        "liquidity_score": score,
    }


if __name__ == "__main__":
    import json

    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.floating, np.integer)):
                return float(obj)
            if isinstance(obj, pd.Timestamp):
                return str(obj)
            return super().default(obj)

    result = run_full_liquidity_assessment()
    print(json.dumps(result, indent=2, cls=NpEncoder))
