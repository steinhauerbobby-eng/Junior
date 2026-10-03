---
name: catalyst
description: Pre-catalyst checklist for options traders. Packages earnings date + DTE, implied move (straddle-based), 8-quarter historical move analysis, implied vs. historical ratio, IV rank/skew/term structure, UOA, and max pain into one command. Usage: /catalyst [TICKER]
when_to_use: Run 5-10 days before a known catalyst (earnings, FDA, macro event). Replaces running /vol and /flow separately for pre-event setup. Follow with /flow for deeper OI analysis if the setup looks interesting after reviewing the catalyst checklist.
---

The user will provide a ticker symbol. Run `full_catalyst_assessment(ticker)` from `src/data/catalyst.py`. Import with `sys.path.insert(0, 'src/data')`.

## Step 1 — Earnings date and DTE
`full_catalyst_assessment()` calls `next_earnings(ticker)` internally.
- Source: yfinance `.calendar` (exchange-confirmed) with fallback to `.info['earningsDate']`
- Returns: earnings_date, DTE, confirmed flag

## Step 2 — Historical earnings moves (8 quarters)
`historical_earnings_moves(ticker, lookback=8)`:
- Pulls yfinance `earnings_dates` for past event dates (requires lxml)
- Computes T-1 to T+1 price move for each event (handles after-hours reporting)
- Returns: per-event table, avg absolute move, up/down count, consistency

## Step 3 — Implied move for earnings expiry
`implied_move_earnings(ticker)`:
- Finds the options expiry closest to the earnings date
- ATM straddle = ATM call lastPrice + ATM put lastPrice
- Implied move % = straddle / current price

## Step 4 — Implied vs. historical ratio
`implied_vs_historical_ratio()`:
- ratio = implied move % / avg historical actual move %
- >1.15: premium expensive | 0.85–1.15: fair | <0.85: premium cheap

## Step 5 — Vol context
`full_vol_assessment(ticker)` from `src/data/volatility.py`:
- IV rank, regime, ATM IV, HV comparison
- 25d risk reversal (skew direction)
- Term structure shape (contango/backwardation)

## Step 6 — Smart money positioning
`unusual_options_activity(ticker)` from `src/data/options_flow.py`:
- UOA filtered toward the earnings expiry window
- Volume/OI ratio, strike, directionality

## Step 7 — Max pain for earnings expiry
`max_pain(ticker, expiry=earnings_expiry)` from `src/data/options_flow.py`:
- Strike where MM obligation is minimized for earnings expiry
- Distance from current price

## Step 8 — Save report
After producing the output below, save the full formatted report to:
`vol reports/catalyst-{TICKER}-{YYYY-MM-DD}.md`
The `vol reports/` directory already exists. Report the file path when done.

## Step 9 — Output

---

## CATALYST CHECKLIST — {TICKER} — {Date}

**{Company Name}** | Price: $XX.XX | Mkt Cap: $X.XB

---

### Catalyst Overview
- **Next earnings:** [Date] — **{X} days away** ([Confirmed / Estimated])
- [Note if unconfirmed: "Verify against IR calendar"]

---

### Implied Move (Earnings Expiry)
- **Expiry used:** [Date] (closest to earnings, {X} DTE)
- **ATM strike:** $XX.XX | Call: $X.XX | Put: $X.XX
- **Straddle cost:** $X.XX per share
- **Implied move: ±X.X%**
- **Implied dollar range:** [$XX.XX – $XX.XX]

---

### Historical Earnings Moves — Last 8 Quarters
| Date | Actual Move | Direction | EPS Surprise |
|---|---|---|---|
| [YYYY-MM-DD] | +X.X% | UP | +X% |
| [YYYY-MM-DD] | -X.X% | DOWN | -X% |
| ... | | | |

- **Average absolute move:** X.X%
- **Range:** X.X% to X.X%
- **Record:** X up / X down over 8 quarters
- **Consistency:** [Directionally consistent / Mixed]

---

### Implied vs. Historical Comparison
| Metric | Value |
|---|---|
| Current implied move | X.X% |
| 8Q average actual move | X.X% |
| **Ratio** | **X.Xx** |

**Assessment:** [Expensive (>1.15) — premium sellers have edge / Fairly priced (0.85–1.15) / Cheap (<0.85) — premium buyers have edge]

[1-2 sentences on what this ratio means for structuring the trade]

---

### Vol Context
| Metric | Value | Signal |
|---|---|---|
| IV Rank (52-week) | XX | [Low / Normal / Elevated / Extreme] |
| ATM IV (30d) | XX% | — |
| HV (20d) | XX% | — |
| IV vs. HV premium | +X% | [Options expensive / cheap vs. realized vol] |
| Term structure | [Contango / Backwardation] | [Near-term event priced in / Normal] |
| 25d Risk Reversal | [+X% / -X%] | [Calls expensive — upside skew / Puts expensive — downside hedging] |

[1-2 sentences: what the combined vol picture implies for premium buying vs. selling]

---

### Smart Money Positioning (UOA — Earnings Window)
[If no unusual activity: "No significant unusual options activity detected near the earnings expiry."]

| Expiry | DTE | Type | Strike | Moneyness | Volume | OI | Vol/OI | IV |
|---|---|---|---|---|---|---|---|---|
| [Date] | X | Call/Put | $XX.XX | +X% OTM | X,XXX | X,XXX | X.Xx | XX% |

**UOA interpretation:** [Is positioning directional? Which way? Does it align or conflict with the implied move structure?]

---

### Max Pain — Earnings Expiry
- **Max pain strike:** $XX.XX (expiry [Date])
- **Distance from current price:** [+X% / -X%]
- **Interpretation:** [Post-earnings gravitational target. If far below current price, MMs will hedge toward it into expiry — relevant if stock makes a modest move on earnings]

---

### Key Inputs Summary
| Input | Value | Reading |
|---|---|---|
| Earnings DTE | X days | — |
| Implied move | X.X% | — |
| Implied / historical ratio | X.Xx | [Expensive / Fair / Cheap] |
| IV Rank | XX | [Low / Normal / Elevated / Extreme] |
| Term structure | [Contango / Backwardation] | — |
| 25d Skew | [+X% / -X%] | [Puts / Calls expensive] |
| UOA direction | [Calls / Puts / Mixed / None] | — |
| Max pain distance | [+X% / -X%] | — |
| Avg historical move | X.X% | vs. X.X% implied |
