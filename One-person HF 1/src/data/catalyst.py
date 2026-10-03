"""
Pre-catalyst checklist for options traders.
Packages earnings timing, implied move, historical move analysis,
IV context, UOA, and max pain into a single assessment.
Used by the /catalyst skill.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf

from volatility import full_vol_assessment
from options_flow import unusual_options_activity, max_pain


# ---------------------------------------------------------------------------
# Earnings date
# ---------------------------------------------------------------------------

def next_earnings(ticker: str) -> dict:
    """Next earnings date, DTE, and confidence level."""
    t = yf.Ticker(ticker)
    earnings_date = None
    confirmed = False

    # Primary: .calendar (most reliable — exchange-confirmed)
    try:
        cal = t.calendar
        if cal is not None:
            # yfinance returns calendar as either a dict or DataFrame depending on version
            if isinstance(cal, dict):
                dates = cal.get("Earnings Date")
                if dates:
                    ed = dates[0] if isinstance(dates, list) else dates
                    if isinstance(ed, datetime):
                        earnings_date = ed.date()
                        confirmed = True
                    elif hasattr(ed, "year"):
                        # datetime.date object — already a date, no .date() method
                        earnings_date = ed
                        confirmed = True
                    elif isinstance(ed, str):
                        earnings_date = datetime.strptime(ed, "%Y-%m-%d").date()
                        confirmed = True
            elif hasattr(cal, "empty") and not cal.empty:
                ed = cal.columns[0]
                if hasattr(ed, "date"):
                    earnings_date = ed.date()
                    confirmed = True
    except Exception:
        pass

    # Fallback: .info earningsDate (list of timestamps)
    if earnings_date is None:
        try:
            ed_raw = t.info.get("earningsDate")
            if ed_raw:
                if isinstance(ed_raw, list) and ed_raw:
                    ed_raw = ed_raw[0]
                if isinstance(ed_raw, (int, float)):
                    earnings_date = datetime.fromtimestamp(ed_raw).date()
                elif hasattr(ed_raw, "date"):
                    earnings_date = ed_raw.date()
        except Exception:
            pass

    if earnings_date is None:
        return {
            "earnings_date": None,
            "dte": None,
            "confirmed": False,
            "note": "Earnings date unavailable — check IR calendar manually",
        }

    dte = (earnings_date - datetime.now().date()).days
    return {
        "earnings_date": str(earnings_date),
        "dte": dte,
        "confirmed": confirmed,
        "note": "Exchange-confirmed" if confirmed else "Estimated from yfinance info — verify against IR calendar",
    }


# ---------------------------------------------------------------------------
# Historical earnings moves
# ---------------------------------------------------------------------------

def historical_earnings_moves(ticker: str, lookback: int = 8) -> dict:
    """
    Actual price moves around the last `lookback` earnings events.
    Uses yfinance earnings_dates for event dates and price history for moves.
    Move = (T+1 close - T-1 close) / T-1 close, where T is the earnings date.
    Handles both after-hours (report on date, move next day) and
    pre-market (report before open, move same day) by using T+1.
    """
    t = yf.Ticker(ticker)

    # Pull earnings history
    try:
        earnings_df = t.earnings_dates
    except Exception:
        return {"error": "Could not retrieve earnings history", "events": [], "count": 0}

    if earnings_df is None or earnings_df.empty:
        return {"error": "No earnings history available", "events": [], "count": 0}

    # Filter to past events only, most recent first
    today = datetime.now().date()
    past = earnings_df[earnings_df.index.normalize() < pd.Timestamp(today, tz="UTC")]
    past = past.sort_index(ascending=False).head(lookback)

    if past.empty:
        return {"error": "No past earnings events found", "events": [], "count": 0}

    # Pull 3Y price history to cover all lookback events
    hist = t.history(period="3y")
    if hist.empty:
        return {"error": "No price history available", "events": [], "count": 0}

    # Normalize price index to date for alignment
    hist.index = hist.index.normalize()
    price_dates = sorted(hist.index.tolist())

    events = []
    for earnings_ts, row in past.iterrows():
        try:
            earnings_date = earnings_ts.date()

            # Find T-1: last trading day strictly before earnings date
            t_minus_1 = [d for d in price_dates if d.date() < earnings_date]
            if not t_minus_1:
                continue
            t_minus_1_date = t_minus_1[-1]

            # Find T+1: first trading day strictly after earnings date
            t_plus_1 = [d for d in price_dates if d.date() > earnings_date]
            if not t_plus_1:
                continue
            t_plus_1_date = t_plus_1[0]

            price_t1 = float(hist.loc[t_minus_1_date, "Close"])
            price_t2 = float(hist.loc[t_plus_1_date, "Close"])
            move_pct = round((price_t2 - price_t1) / price_t1 * 100, 2)

            # EPS surprise if available
            eps_surprise = None
            if "Surprise(%)" in row.index and pd.notna(row["Surprise(%)"]):
                eps_surprise = round(float(row["Surprise(%)"]), 1)

            events.append({
                "date": str(earnings_date),
                "actual_move_pct": move_pct,
                "direction": "UP" if move_pct >= 0 else "DOWN",
                "abs_move_pct": round(abs(move_pct), 2),
                "eps_surprise_pct": eps_surprise,
            })
        except Exception:
            continue

    if not events:
        return {"error": "Could not compute moves for any earnings event", "events": [], "count": 0}

    abs_moves = [e["abs_move_pct"] for e in events]
    up_count = sum(1 for e in events if e["direction"] == "UP")
    down_count = len(events) - up_count

    dominant = "UP" if up_count > down_count else "DOWN" if down_count > up_count else "MIXED"
    consistency = (
        "Directionally consistent" if max(up_count, down_count) >= round(len(events) * 0.75)
        else "Mixed directional history"
    )

    return {
        "events": events,
        "count": len(events),
        "avg_absolute_move_pct": round(float(np.mean(abs_moves)), 2),
        "max_absolute_move_pct": round(float(np.max(abs_moves)), 2),
        "min_absolute_move_pct": round(float(np.min(abs_moves)), 2),
        "up_count": up_count,
        "down_count": down_count,
        "dominant_direction": dominant,
        "consistency": consistency,
    }


# ---------------------------------------------------------------------------
# Implied move for earnings expiry
# ---------------------------------------------------------------------------

def implied_move_earnings(ticker: str, earnings_date_str: str | None = None) -> dict:
    """
    ATM straddle cost for the options expiry closest to the earnings date.
    Implied move % = (ATM call + ATM put last price) / current price.
    """
    t = yf.Ticker(ticker)
    expirations = t.options
    if not expirations:
        return {"error": f"No options data for {ticker}"}

    # Determine target date
    if earnings_date_str:
        try:
            target_date = datetime.strptime(earnings_date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = (datetime.now() + timedelta(days=30)).date()
    else:
        target_date = (datetime.now() + timedelta(days=30)).date()

    # Find expiry closest to (and ideally just after) the earnings date
    def expiry_distance(exp_str: str) -> int:
        exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
        return abs((exp_date - target_date).days)

    expiry = min(expirations, key=expiry_distance)
    dte_to_expiry = (datetime.strptime(expiry, "%Y-%m-%d").date() - datetime.now().date()).days

    chain = t.option_chain(expiry)
    price = t.info.get("regularMarketPrice") or float(t.history(period="1d")["Close"].iloc[-1])

    calls = chain.calls.copy()
    puts = chain.puts.copy()
    calls["dist"] = (calls["strike"] - price).abs()
    puts["dist"] = (puts["strike"] - price).abs()

    atm_call = calls.nsmallest(1, "dist").iloc[0]
    atm_put = puts.nsmallest(1, "dist").iloc[0]

    atm_call_price = round(float(atm_call["lastPrice"]), 2)
    atm_put_price = round(float(atm_put["lastPrice"]), 2)
    straddle_cost = round(atm_call_price + atm_put_price, 2)
    implied_move_pct = round(straddle_cost / price * 100, 2)
    implied_move_dollars = round(straddle_cost, 2)

    return {
        "expiry": expiry,
        "dte_to_expiry": dte_to_expiry,
        "atm_strike": round(float(atm_call["strike"]), 2),
        "atm_call_price": atm_call_price,
        "atm_put_price": atm_put_price,
        "straddle_cost": straddle_cost,
        "implied_move_pct": implied_move_pct,
        "implied_move_dollars": implied_move_dollars,
        "price_range_low": round(price - straddle_cost, 2),
        "price_range_high": round(price + straddle_cost, 2),
    }


# ---------------------------------------------------------------------------
# Quarterly delta (for earningsrecap Earnings Delta section)
# ---------------------------------------------------------------------------

def quarterly_delta(ticker: str) -> dict:
    """
    YoY changes in key income statement metrics (same quarter prior year).
    Uses quarterly_income_stmt columns[0] vs columns[4] for same-quarter comparison.
    Falls back to columns[1] (QoQ) if fewer than 5 quarters of data are available.
    Used by the /earningsrecap Earnings Delta section.
    """
    t = yf.Ticker(ticker)

    try:
        stmt = t.quarterly_income_stmt
    except Exception:
        return {"ticker": ticker, "error": "Could not retrieve quarterly_income_stmt"}

    if stmt is None or stmt.empty or stmt.shape[1] < 2:
        return {"ticker": ticker, "error": "Insufficient quarterly data (need at least 2 quarters)"}

    # YoY: most recent quarter vs. same quarter one year ago (4 quarters back)
    cur_col = stmt.columns[0]
    has_yoy = stmt.shape[1] >= 5
    pri_col = stmt.columns[4] if has_yoy else stmt.columns[1]
    comparison = "YoY" if has_yoy else "QoQ (insufficient history for YoY)"
    cur_q = str(cur_col.date()) if hasattr(cur_col, "date") else str(cur_col)[:10]
    pri_q = str(pri_col.date()) if hasattr(pri_col, "date") else str(pri_col)[:10]

    def _val(row_label: str, col) -> float | None:
        if row_label in stmt.index:
            v = stmt.loc[row_label, col]
            return float(v) if pd.notna(v) else None
        return None

    def _delta(cur: float | None, pri: float | None) -> dict:
        if cur is None or pri is None:
            return {"prior": pri, "current": cur, "change_pct": None, "change_abs": None}
        change_abs = round(cur - pri, 0)
        change_pct = round((cur - pri) / abs(pri) * 100, 1) if pri != 0 else None
        return {
            "prior": round(pri, 0),
            "current": round(cur, 0),
            "change_pct": change_pct,
            "change_abs": change_abs,
        }

    def _margin_delta(profit: float | None, revenue: float | None,
                      prior_profit: float | None, prior_revenue: float | None) -> dict:
        cur_m = round(profit / revenue * 100, 2) if profit and revenue else None
        pri_m = round(prior_profit / prior_revenue * 100, 2) if prior_profit and prior_revenue else None
        bps = round((cur_m - pri_m) * 100) if cur_m is not None and pri_m is not None else None
        return {"prior_pct": pri_m, "current_pct": cur_m, "change_bps": bps}

    cur_rev = _val("Total Revenue", cur_col)
    pri_rev = _val("Total Revenue", pri_col)
    cur_gp = _val("Gross Profit", cur_col)
    pri_gp = _val("Gross Profit", pri_col)
    cur_ebitda = _val("EBITDA", cur_col)
    pri_ebitda = _val("EBITDA", pri_col)
    cur_ni = _val("Net Income", cur_col)
    pri_ni = _val("Net Income", pri_col)

    # EPS YoY: use earnings_dates (8+ quarters) for same-quarter prior year comparison
    eps_cur = eps_pri = None
    try:
        ed = t.earnings_dates
        if ed is not None and not ed.empty and "Reported EPS" in ed.columns:
            today = datetime.now().date()
            past = ed[ed.index.normalize() < pd.Timestamp(today, tz="UTC")]
            past = past.sort_index(ascending=False)
            eps_vals = past["Reported EPS"].dropna()
            if len(eps_vals) >= 1:
                eps_cur = round(float(eps_vals.iloc[0]), 4)
            # index 4 = same quarter prior year
            prior_idx = 4 if len(eps_vals) >= 5 else (1 if len(eps_vals) >= 2 else None)
            if prior_idx is not None:
                eps_pri = round(float(eps_vals.iloc[prior_idx]), 4)
    except Exception:
        pass

    eps_change = round(eps_cur - eps_pri, 4) if eps_cur is not None and eps_pri is not None else None

    return {
        "ticker": ticker,
        "current_quarter": cur_q,
        "prior_year_quarter": pri_q,
        "comparison": comparison,
        "revenue": _delta(cur_rev, pri_rev),
        "gross_margin": _margin_delta(cur_gp, cur_rev, pri_gp, pri_rev),
        "ebitda": _delta(cur_ebitda, pri_ebitda),
        "ebitda_margin": _margin_delta(cur_ebitda, cur_rev, pri_ebitda, pri_rev),
        "net_income": _delta(cur_ni, pri_ni),
        "eps": {"prior": eps_pri, "current": eps_cur, "change": eps_change},
    }


# ---------------------------------------------------------------------------
# EPS surprise history (for earningsrecap Revision Drivers section)
# ---------------------------------------------------------------------------

def earnings_surprise_history(ticker: str, lookback: int = 8) -> dict:
    """
    EPS actual vs. estimate and surprise % for the last `lookback` quarters.
    Used by the /earningsrecap Revision Drivers section.
    Source: yfinance earnings_dates (requires lxml).
    """
    t = yf.Ticker(ticker)
    try:
        df = t.earnings_dates
    except Exception:
        return {"ticker": ticker, "error": "Could not retrieve earnings_dates (lxml required)", "quarters": [], "count": 0}

    if df is None or df.empty:
        return {"ticker": ticker, "error": "No earnings history", "quarters": [], "count": 0}

    today = datetime.now().date()
    past = df[df.index.normalize() < pd.Timestamp(today, tz="UTC")]
    past = past.sort_index(ascending=False).head(lookback)

    quarters = []
    for ts, row in past.iterrows():
        est = row.get("EPS Estimate")
        act = row.get("Reported EPS")
        surp = row.get("Surprise(%)")

        est_val = round(float(est), 4) if pd.notna(est) else None
        act_val = round(float(act), 4) if pd.notna(act) else None
        surp_val = round(float(surp), 1) if pd.notna(surp) else None

        if surp_val is not None:
            bom = "BEAT" if surp_val > 2 else "MISS" if surp_val < -2 else "IN-LINE"
        elif est_val is not None and act_val is not None:
            diff_pct = (act_val - est_val) / abs(est_val) * 100 if est_val != 0 else 0
            bom = "BEAT" if diff_pct > 2 else "MISS" if diff_pct < -2 else "IN-LINE"
        else:
            bom = "N/A"

        quarters.append({
            "date": str(ts.date()),
            "eps_estimate": est_val,
            "eps_actual": act_val,
            "surprise_pct": surp_val,
            "beat_or_miss": bom,
        })

    if not quarters:
        return {"ticker": ticker, "quarters": [], "count": 0}

    # Streak: how many consecutive beats or misses from most recent
    streak_val = 0
    first_bom = quarters[0]["beat_or_miss"]
    if first_bom in ("BEAT", "MISS"):
        for q in quarters:
            if q["beat_or_miss"] == first_bom:
                streak_val += 1
            else:
                break
    consecutive_beats = streak_val if first_bom == "BEAT" else 0
    consecutive_misses = streak_val if first_bom == "MISS" else 0

    # Average surprise
    valid_surps = [q["surprise_pct"] for q in quarters if q["surprise_pct"] is not None]
    avg_surprise = round(float(np.mean(valid_surps)), 1) if valid_surps else None

    # Trend
    beat_count = sum(1 for q in quarters if q["beat_or_miss"] == "BEAT")
    miss_count = sum(1 for q in quarters if q["beat_or_miss"] == "MISS")
    n = len(quarters)
    if beat_count >= round(n * 0.75):
        trend = "Consistent beater"
    elif miss_count >= round(n * 0.75):
        trend = "Consistent miss"
    elif consecutive_beats >= 3:
        trend = "Improving — recent beat streak"
    elif consecutive_misses >= 3:
        trend = "Declining — recent miss streak"
    else:
        trend = "Volatile — mixed beat/miss history"

    return {
        "ticker": ticker,
        "quarters": quarters,
        "count": len(quarters),
        "avg_surprise_pct": avg_surprise,
        "consecutive_beats": consecutive_beats,
        "consecutive_misses": consecutive_misses,
        "surprise_trend": trend,
    }


# ---------------------------------------------------------------------------
# Implied vs. historical ratio
# ---------------------------------------------------------------------------

def implied_vs_historical_ratio(implied_move_pct: float, avg_historical_move_pct: float) -> dict:
    """
    Compare current implied move to historical average actual move.
    ratio > 1.15 = premium expensive; < 0.85 = premium cheap.
    """
    if avg_historical_move_pct <= 0:
        return {"error": "Invalid historical average move", "ratio": None}

    ratio = round(implied_move_pct / avg_historical_move_pct, 3)

    if ratio > 1.15:
        assessment = "Expensive — market pricing a larger move than history supports; premium sellers have edge"
    elif ratio < 0.85:
        assessment = "Cheap — market underpricing this event vs. historical moves; premium buyers have edge"
    else:
        assessment = "Fairly priced — implied move consistent with historical average"

    return {
        "ratio": ratio,
        "assessment": assessment,
        "implied_move_pct": implied_move_pct,
        "avg_historical_move_pct": avg_historical_move_pct,
    }


# ---------------------------------------------------------------------------
# Full orchestrator
# ---------------------------------------------------------------------------

def full_catalyst_assessment(ticker: str) -> dict:
    """Single entry point for the /catalyst skill."""
    t = yf.Ticker(ticker)
    price = t.info.get("regularMarketPrice") or float(t.history(period="1d")["Close"].iloc[-1])
    name = t.info.get("shortName") or t.info.get("longName") or ticker
    mktcap = t.info.get("marketCap")

    # Step 1 — earnings date
    earnings = next_earnings(ticker)
    earnings_date_str = earnings.get("earnings_date")

    # Step 2 — historical moves
    hist_moves = historical_earnings_moves(ticker, lookback=8)

    # Step 3 — implied move for earnings expiry
    implied = implied_move_earnings(ticker, earnings_date_str=earnings_date_str)

    # Step 4 — implied vs historical ratio
    ivh = {"ratio": None, "assessment": "Insufficient data"}
    if "error" not in implied and "error" not in hist_moves and hist_moves.get("avg_absolute_move_pct"):
        ivh = implied_vs_historical_ratio(
            implied["implied_move_pct"],
            hist_moves["avg_absolute_move_pct"],
        )

    # Step 5 — full vol assessment (IV rank, skew, term structure)
    vol = full_vol_assessment(ticker)

    # Step 6 — UOA (filter toward earnings expiry if possible)
    uoa = unusual_options_activity(ticker)

    # Step 7 — max pain for earnings expiry
    mp = {}
    if "error" not in implied:
        mp = max_pain(ticker, expiry=implied.get("expiry"))

    return {
        "ticker": ticker,
        "company_name": name,
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "current_price": round(float(price), 2),
        "market_cap_b": round(mktcap / 1e9, 2) if mktcap else None,
        "earnings": earnings,
        "historical_moves": hist_moves,
        "implied_move": implied,
        "implied_vs_historical": ivh,
        "vol": vol,
        "uoa": uoa,
        "max_pain": mp,
    }
