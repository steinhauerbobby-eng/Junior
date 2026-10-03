---
name: vol
description: Volatility assessment for a ticker. Calculates 20/30/60-day historical volatility, ATM implied volatility, IV rank/percentile, volatility skew (25-delta risk reversal), and IV term structure. Usage: /vol [TICKER]
when_to_use: Use when assessing whether options are cheap or expensive, sizing a position based on volatility, or structuring an options trade. Run before /flow for a complete options picture.
---

The user will provide a ticker symbol. Use `src/data/volatility.py` and yfinance to run the full volatility assessment via `full_vol_assessment(ticker)`.

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

## Step 4 — Volatility Skew
Call `volatility_skew(ticker)` from `src/data/volatility.py`:
- Find the 25-delta call and put (using Black-Scholes delta, expiry closest to 30 days)
- **Risk reversal** = 25-delta call IV − 25-delta put IV
  - Positive: calls more expensive → upside skew / squeeze risk
  - Negative: puts more expensive → normal equity downside hedging
- **Butterfly** = (25d call IV + 25d put IV) / 2 − ATM IV → measures wing premium vs. center

## Step 5 — IV Term Structure
Call `iv_term_structure(ticker)` from `src/data/volatility.py`:
- Pull ATM IV for expiries closest to 7, 30, 60, and 90 days
- Determine curve shape: contango (normal) vs. backwardation (near-term event risk)
- Flag calendar spread opportunity if front-week IV is >10% above 30-day IV

## Step 6 — Store snapshot
Insert current IV reading into `iv_snapshots` table: (ticker, date, iv_30d_atm, hv_20d, hv_30d, hv_60d)

## Step 7 — Save report
After producing the output below, save the full formatted report to:
`vol reports/vol-{TICKER}-{YYYY-MM-DD}.md`
Create the `vol reports/` directory if it doesn't exist. Report the file path when done.

## Step 8 — Output

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

### Volatility Skew (25-Delta)
| Metric | Strike | Delta | IV |
|---|---|---|---|
| 25-delta Call | $XX.XX | +0.XX | XX% |
| ATM | $XX.XX | ~0.50 | XX% |
| 25-delta Put | $XX.XX | -0.XX | XX% |

- **Risk Reversal (25d RR):** [+X% / -X%]
  - [Positive: calls expensive → upside skew / Negative: puts expensive → normal equity skew]
- **25d Butterfly:** [+X%] — [fat wings / normal / compressed wings]
- **Skew interpretation:** [What does the skew tell you about market positioning and which direction is cheaper to buy?]

### IV Term Structure
| Tenor | Expiry | DTE | ATM IV |
|---|---|---|---|
| ~7-day | [Date] | X | XX% |
| ~30-day | [Date] | X | XX% |
| ~60-day | [Date] | X | XX% |
| ~90-day | [Date] | X | XX% |

- **Curve shape:** [Contango / Backwardation / Flat]
- **Interpretation:** [What the term structure shape means for DTE selection and structure choice]
- **Calendar opportunity:** [Flag if present — e.g., "7d IV at XX% vs. 30d at XX% — front significantly elevated, calendar spread opportunity"]

### Options Strategy Implications
[3-4 bullet points synthesizing ALL of the above into actionable structure guidance:]
- **Buy or sell premium?** [Based on IV rank + HV/IV relationship]
- **DTE selection:** [Based on term structure shape and catalyst timing]
- **Strike selection / skew edge:** [Which direction is cheaper given the risk reversal]
- **Suggested structure:** [e.g., "Long call spread 30-45 DTE — IV elevated but directional; spread reduces vega drag" or "Long straddle — IV cheap, event approaching, backwardation"]

### Bottom Line
[2-3 sentences: is vol cheap or expensive? What does this imply for options strategy? Any notable divergence between HV and IV, or meaningful skew/term structure signal?]
