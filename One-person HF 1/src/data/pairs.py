"""
Long/short pairs analysis: correlation, spread z-score, cointegration, mean-reversion
half-life, beta-neutral sizing, relative valuation, IV ratio, and earnings alignment.
Used by the /pairs skill.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats
from statsmodels.tsa.stattools import adfuller, coint

from volatility import implied_volatility


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_info(ticker: str) -> dict:
    return yf.Ticker(ticker).info


def _sync_prices(ticker1: str, ticker2: str, period: str = "1y") -> tuple[pd.Series, pd.Series]:
    """Pull daily closes for both tickers and align on common trading dates."""
    t1 = yf.Ticker(ticker1).history(period=period)["Close"].rename(ticker1)
    t2 = yf.Ticker(ticker2).history(period=period)["Close"].rename(ticker2)
    df = pd.concat([t1, t2], axis=1).dropna()
    return df[ticker1], df[ticker2]


def _log_returns(series: pd.Series) -> pd.Series:
    return np.log(series / series.shift(1)).dropna()


# ---------------------------------------------------------------------------
# Correlation
# ---------------------------------------------------------------------------

def correlation_analysis(ticker1: str, ticker2: str) -> dict:
    p1, p2 = _sync_prices(ticker1, ticker2, period="1y")
    r1 = _log_returns(p1)
    r2 = _log_returns(p2)

    def rolling_corr(w: int) -> float | None:
        if len(r1) < w:
            return None
        return round(float(r1.rolling(w).corr(r2).iloc[-1]), 3)

    corr_20 = rolling_corr(20)
    corr_60 = rolling_corr(60)
    corr_90 = rolling_corr(90)

    # Trend: compare last-30d correlation to prior-30d correlation
    trend = "insufficient data"
    if len(r1) >= 60:
        recent = float(r1.iloc[-30:].corr(r2.iloc[-30:]))
        prior = float(r1.iloc[-60:-30].corr(r2.iloc[-60:-30]))
        delta = recent - prior
        trend = "increasing" if delta > 0.05 else "decreasing" if delta < -0.05 else "stable"

    if corr_90 is not None:
        interp = (
            "Strong — pair moves tightly together, good candidate for spread trading"
            if corr_90 >= 0.70
            else "Moderate — decent correlation but spread may be noisy"
            if corr_90 >= 0.45
            else "Weak — low correlation, high residual risk in this pair"
        )
    else:
        interp = "Insufficient data"

    return {
        "corr_20d": corr_20,
        "corr_60d": corr_60,
        "corr_90d": corr_90,
        "trend": trend,
        "interpretation": interp,
    }


# ---------------------------------------------------------------------------
# Spread: hedge ratio, z-score, half-life, ADF
# ---------------------------------------------------------------------------

def spread_analysis(ticker1: str, ticker2: str, window: int = 60) -> dict:
    p1, p2 = _sync_prices(ticker1, ticker2, period="2y")
    log_p1 = np.log(p1)
    log_p2 = np.log(p2)

    # OLS hedge ratio: log_p1 = alpha + beta * log_p2
    slope, intercept, *_ = stats.linregress(log_p2, log_p1)
    hedge_ratio = round(float(slope), 4)
    spread = log_p1 - hedge_ratio * log_p2 - intercept

    # Rolling z-score
    roll_mean = spread.rolling(window).mean()
    roll_std = spread.rolling(window).std()
    z_series = (spread - roll_mean) / roll_std
    z_score = round(float(z_series.iloc[-1]), 3)

    # Mean-reversion half-life (Ornstein-Uhlenbeck)
    delta_spread = spread.diff().dropna()
    lagged = spread.shift(1).dropna()
    lagged, delta_spread = lagged.align(delta_spread, join="inner")
    ou_slope, *_ = stats.linregress(lagged, delta_spread)
    half_life = None
    if ou_slope < 0:
        half_life = round(float(-np.log(2) / ou_slope), 1)

    # ADF test for stationarity of spread
    adf_result = adfuller(spread.dropna(), autolag="AIC")
    adf_pvalue = round(float(adf_result[1]), 4)
    stationary = adf_pvalue < 0.05

    # Trade signal
    if z_score > 2.0:
        signal = f"SHORT SPREAD — short {ticker1}, long {ticker2} (z={z_score:.2f}, stretched +2 std dev)"
    elif z_score < -2.0:
        signal = f"LONG SPREAD — long {ticker1}, short {ticker2} (z={z_score:.2f}, stretched -2 std dev)"
    elif abs(z_score) < 0.5:
        signal = f"NEUTRAL / EXIT ZONE — spread near mean (z={z_score:.2f})"
    else:
        signal = f"NO SIGNAL — z={z_score:.2f}, wait for +/-2 std dev entry"

    # Recent spread context (last 5 values)
    recent = [
        {"date": str(d.date()), "spread": round(float(s), 4), "z": round(float(z), 2)}
        for d, s, z in zip(spread.index[-5:], spread.iloc[-5:], z_series.iloc[-5:])
    ]

    return {
        "hedge_ratio": hedge_ratio,
        "current_spread": round(float(spread.iloc[-1]), 4),
        "z_score": z_score,
        "z_window_days": window,
        "half_life_days": half_life,
        "adf_pvalue": adf_pvalue,
        "stationary": stationary,
        "signal": signal,
        "recent_spread": recent,
    }


# ---------------------------------------------------------------------------
# Cointegration (Engle-Granger)
# ---------------------------------------------------------------------------

def cointegration_test(ticker1: str, ticker2: str) -> dict:
    p1, p2 = _sync_prices(ticker1, ticker2, period="2y")
    t_stat, p_value, crit_values = coint(p1, p2)

    cointegrated = bool(p_value < 0.05)
    interpretation = (
        f"COINTEGRATED (p={p_value:.4f}) — spread has a stable long-run mean; deviations are temporary and should revert"
        if cointegrated
        else f"NOT COINTEGRATED (p={p_value:.4f}) — no stable long-run relationship detected; spread may trend away permanently"
    )

    return {
        "t_statistic": round(float(t_stat), 4),
        "p_value": round(float(p_value), 4),
        "critical_values": {
            "1pct": round(float(crit_values[0]), 4),
            "5pct": round(float(crit_values[1]), 4),
            "10pct": round(float(crit_values[2]), 4),
        },
        "cointegrated": cointegrated,
        "interpretation": interpretation,
    }


# ---------------------------------------------------------------------------
# Beta-neutral sizing
# ---------------------------------------------------------------------------

def beta_neutral_sizing(ticker1: str, ticker2: str) -> dict:
    info1 = _get_info(ticker1)
    info2 = _get_info(ticker2)

    beta1 = info1.get("beta")
    beta2 = info2.get("beta")

    if beta1 is None or beta2 is None or beta2 == 0:
        return {
            "beta1": beta1,
            "beta2": beta2,
            "beta_neutral_ratio": None,
            "dollar_neutral_ratio": 1.0,
            "net_beta_after_hedge": None,
            "note": "Beta unavailable for one or both tickers — use dollar-neutral sizing as fallback",
        }

    beta1 = round(float(beta1), 3)
    beta2 = round(float(beta2), 3)
    ratio = round(beta1 / beta2, 3)
    net_beta = round(beta1 - ratio * beta2, 4)

    reliability_flag = None
    if abs(beta1) > 3.0 or abs(beta2) > 3.0:
        reliability_flag = "High beta values — yfinance beta may be unreliable for small-cap or thinly traded names; consider using 60d realized beta"

    return {
        "beta1": beta1,
        "beta2": beta2,
        "beta_neutral_ratio": ratio,
        "dollar_neutral_ratio": 1.0,
        "net_beta_after_hedge": net_beta,
        "interpretation": (
            f"For every $1.00 long {ticker1}, short ${ratio:.2f} in {ticker2} to achieve market-neutral exposure. "
            f"Residual net beta ≈ {net_beta:.3f} vs. SPY."
        ),
        "reliability_flag": reliability_flag,
    }


# ---------------------------------------------------------------------------
# Relative valuation
# ---------------------------------------------------------------------------

def relative_valuation(ticker1: str, ticker2: str) -> dict:
    info1 = _get_info(ticker1)
    info2 = _get_info(ticker2)

    def _spread(key: str) -> dict:
        v1 = info1.get(key)
        v2 = info2.get(key)
        if v1 is None or v2 is None:
            return {"ticker1": None, "ticker2": None, "spread": None, "cheaper": None}
        v1, v2 = float(v1), float(v2)
        spread_val = round(v1 - v2, 2)
        cheaper = ticker2 if v1 > v2 else ticker1
        return {
            "ticker1": round(v1, 2),
            "ticker2": round(v2, 2),
            "spread": spread_val,
            "cheaper": cheaper,
        }

    pe = _spread("forwardPE")
    ev_ebitda = _spread("enterpriseToEbitda")
    ev_revenue = _spread("enterpriseToRevenue")
    p_book = _spread("priceToBook")

    # 2Y price ratio z-score as valuation divergence proxy
    p1, p2 = _sync_prices(ticker1, ticker2, period="2y")
    price_ratio = p1 / p2
    pr_mean = price_ratio.mean()
    pr_std = price_ratio.std()
    pr_current = float(price_ratio.iloc[-1])
    pr_zscore = round((pr_current - float(pr_mean)) / float(pr_std), 2)

    pr_signal = (
        f"{ticker1} historically expensive vs. {ticker2} (ratio +{pr_zscore:.1f}σ above 2Y mean)"
        if pr_zscore > 1.5
        else f"{ticker1} historically cheap vs. {ticker2} (ratio {pr_zscore:.1f}σ below 2Y mean)"
        if pr_zscore < -1.5
        else "Price ratio near 2Y historical mean — no extreme valuation divergence"
    )

    # Overall cheaper name across available metrics
    cheaper_votes: dict[str, int] = {}
    for m in [pe, ev_ebitda, ev_revenue, p_book]:
        if m["cheaper"]:
            cheaper_votes[m["cheaper"]] = cheaper_votes.get(m["cheaper"], 0) + 1
    overall_cheaper = max(cheaper_votes, key=cheaper_votes.get) if cheaper_votes else None

    return {
        "forward_pe": pe,
        "ev_ebitda": ev_ebitda,
        "ev_revenue": ev_revenue,
        "price_to_book": p_book,
        "price_ratio_2y_zscore": pr_zscore,
        "price_ratio_signal": pr_signal,
        "overall_cheaper_name": overall_cheaper,
    }


# ---------------------------------------------------------------------------
# IV ratio
# ---------------------------------------------------------------------------

def iv_ratio_analysis(ticker1: str, ticker2: str) -> dict:
    iv1_data = implied_volatility(ticker1)
    iv2_data = implied_volatility(ticker2)

    if "error" in iv1_data or "error" in iv2_data:
        return {
            "error": iv1_data.get("error") or iv2_data.get("error"),
            "iv1": None,
            "iv2": None,
        }

    iv1 = iv1_data["atm_iv"]
    iv2 = iv2_data["atm_iv"]
    ratio = round(iv1 / iv2, 3) if iv2 > 0 else None
    cheaper_leg = ticker2 if iv1 >= iv2 else ticker1
    dearer_leg = ticker1 if iv1 >= iv2 else ticker2
    iv_spread = round(abs(iv1 - iv2), 2)

    if ratio and ratio > 1.15:
        implication = (
            f"{ticker1} options {round((ratio-1)*100, 1)}% more expensive than {ticker2}. "
            f"Favor buying options on {ticker2} (cheaper vol); sell premium on {ticker1} side. "
            f"For a directional pair: buy calls/puts on {ticker2}, sell spreads on {ticker1}."
        )
    elif ratio and ratio < 0.87:
        implication = (
            f"{ticker2} options {round((1/ratio-1)*100, 1)}% more expensive than {ticker1}. "
            f"Favor buying options on {ticker1} (cheaper vol); sell premium on {ticker2} side."
        )
    else:
        implication = (
            f"IV roughly equal between both legs ({iv1:.1f}% vs {iv2:.1f}%). "
            f"No vol-based structural edge — size both legs symmetrically."
        )

    return {
        "iv1": iv1,
        "iv1_expiry": iv1_data["expiry"],
        "iv2": iv2,
        "iv2_expiry": iv2_data["expiry"],
        "iv_ratio": ratio,
        "iv_spread_pts": iv_spread,
        "cheaper_options_leg": cheaper_leg,
        "dearer_options_leg": dearer_leg,
        "implication": implication,
    }


# ---------------------------------------------------------------------------
# Earnings alignment
# ---------------------------------------------------------------------------

def earnings_alignment(ticker1: str, ticker2: str) -> dict:
    results = {}
    for ticker in [ticker1, ticker2]:
        t = yf.Ticker(ticker)
        earnings_date = None
        dte = None
        try:
            cal = t.calendar
            if cal is not None and not cal.empty:
                # calendar is a DataFrame with columns as dates; first column = next earnings
                ed = cal.columns[0]
                if hasattr(ed, "date"):
                    earnings_date = str(ed.date())
                    dte = (ed.date() - datetime.now().date()).days
        except Exception:
            pass

        if earnings_date is None:
            try:
                ed_raw = t.info.get("earningsDate") or t.info.get("earningsTimestamp")
                if ed_raw:
                    if isinstance(ed_raw, (int, float)):
                        ed = datetime.fromtimestamp(ed_raw)
                    elif isinstance(ed_raw, list) and ed_raw:
                        ed = ed_raw[0] if isinstance(ed_raw[0], datetime) else datetime.fromtimestamp(ed_raw[0])
                    else:
                        ed = ed_raw
                    earnings_date = str(ed.date()) if hasattr(ed, "date") else str(ed)
                    dte_calc = (ed.date() - datetime.now().date()).days if hasattr(ed, "date") else None
                    dte = dte_calc
            except Exception:
                pass

        results[ticker] = {"earnings_date": earnings_date, "dte": dte}

    dte1 = results[ticker1]["dte"]
    dte2 = results[ticker2]["dte"]
    gap = abs(dte1 - dte2) if dte1 is not None and dte2 is not None else None
    event_risk_flag = gap is not None and gap > 14

    note = None
    if event_risk_flag:
        earlier = ticker1 if (dte1 or 999) < (dte2 or 999) else ticker2
        note = (
            f"Earnings {gap} days apart — {earlier} reports first, creating {gap}-day window of "
            f"unhedged single-leg event risk. Consider sizing down or waiting until both have reported."
        )
    elif gap is not None:
        note = f"Earnings within {gap} days of each other — event risk is well-matched across both legs."
    else:
        note = "Earnings dates unavailable for one or both tickers."

    return {
        ticker1: results[ticker1],
        ticker2: results[ticker2],
        "gap_days": gap,
        "event_risk_flag": event_risk_flag,
        "note": note,
    }


# ---------------------------------------------------------------------------
# Full orchestrator
# ---------------------------------------------------------------------------

def full_pairs_analysis(ticker1: str, ticker2: str) -> dict:
    t1 = yf.Ticker(ticker1)
    t2 = yf.Ticker(ticker2)
    price1 = float(t1.history(period="1d")["Close"].iloc[-1])
    price2 = float(t2.history(period="1d")["Close"].iloc[-1])

    return {
        "ticker1": ticker1,
        "ticker2": ticker2,
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "current_prices": {
            ticker1: round(price1, 2),
            ticker2: round(price2, 2),
        },
        "correlation": correlation_analysis(ticker1, ticker2),
        "spread": spread_analysis(ticker1, ticker2),
        "cointegration": cointegration_test(ticker1, ticker2),
        "beta_sizing": beta_neutral_sizing(ticker1, ticker2),
        "valuation": relative_valuation(ticker1, ticker2),
        "iv": iv_ratio_analysis(ticker1, ticker2),
        "earnings": earnings_alignment(ticker1, ticker2),
    }
