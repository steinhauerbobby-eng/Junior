---
name: vol
description: Volatility assessment for a ticker. Calculates 20/30/60-day historical volatility, pulls ATM implied volatility from the options chain, computes IV rank and IV percentile from stored snapshots, and assesses the current vol regime. Usage: /vol [TICKER]
when_to_use: Use when assessing whether options are cheap or expensive, sizing a position based on volatility, or understanding the vol regime before entering a trade.
---

The user will provide a ticker symbol. Use `src/data/volatility.py` and yfinance to run the full volatility assessment.

## Step 1 — Historical Volatility
Use yfinance to pull 1 year of daily close prices. Calculate:
- 20-day HV (annualized): rolling 20-day std of log returns × √252
- 30-day HV (annualized): rolling 30-day std of log returns × √252
- 60-day HV (annualized): rolling 60-day std of log returns × √252

## Step 2 — Implied Volatility
Use yfinance options chain:
- Find the expiry closest to 30 days out
- Find the ATM call and put (strike closest to current price)
- Record the implied volatility from both; use the average as the 30-day ATM IV

## Step 3 — IV Rank & IV Percentile
Query `data/hedge_fund.db` (iv_snapshots table) for historical IV readings for this ticker.
- **IV Rank**: (Current IV - 52-week low IV) / (52-week high IV - 52-week low IV) × 100
- **IV Percentile**: % of days in the past 52 weeks where IV was below current IV

If fewer than 30 snapshots exist, note that IV rank/percentile data is limited.

## Step 4 — Store snapshot
Insert current IV reading into `iv_snapshots` table: (ticker, date, iv_30d_atm, hv_20d, hv_30d, hv_60d)

## Step 5 — Output

---

## VOL ASSESSMENT — {TICKER} — {Date}

**Current Price:** $XX.XX

### Historical Volatility
| Window | HV (Annualized) |
|---|---|
| 20-day | XX% |
| 30-day | XX% |
| 60-day | XX% |

### Implied Volatility
| Metric | Value |
|---|---|
| ATM IV (30-day) | XX% |
| Expiry used | [Date] |
| Strike used | $XX.XX |

### HV vs. IV
- IV Premium/Discount to 30d HV: [+X% premium / -X% discount]
- Interpretation: [Options are expensive / fairly priced / cheap relative to realized vol]

### IV Rank & Percentile
| Metric | Value | Data quality |
|---|---|---|
| IV Rank (52-week) | XX | [X days of history] |
| IV Percentile (52-week) | XX% | [X days of history] |

**Vol Regime:** [Low / Normal / Elevated / Extreme]
- IV Rank <25: Low — options are cheap, buyers favored
- IV Rank 25-50: Normal
- IV Rank 50-75: Elevated — sellers have edge
- IV Rank >75: Extreme — options expensive, consider selling premium

### Bottom Line
[2-3 sentences: is vol cheap or expensive? What does this imply for position sizing or options strategy? Any notable divergence between HV and IV?]
