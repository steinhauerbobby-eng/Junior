---
name: pairs
description: Long/short pairs analysis for two tickers. Covers spread z-score, cointegration, mean-reversion half-life, beta-neutral sizing, relative valuation, IV ratio, and earnings alignment. Usage: /pairs TICKER1 TICKER2
when_to_use: Use when structuring a long/short pair trade to minimize beta exposure. Run after /light on both names. Produces sizing ratio, entry signal, and options structure recommendation.
---

The user will provide two ticker symbols. Run `full_pairs_analysis(ticker1, ticker2)` from `src/data/pairs.py`. Import with `sys.path.insert(0, 'src/data')`.

## Step 1 — Synchronized price history
Pull 1Y (correlation) and 2Y (spread/cointegration) daily close prices for both tickers, aligned on common trading dates.

## Step 2 — Correlation analysis
Call `correlation_analysis(ticker1, ticker2)`:
- Rolling 20d, 60d, 90d Pearson correlation on log returns
- Trend (increasing / stable / decreasing) vs. prior 30-day window

## Step 3 — Spread analysis
Call `spread_analysis(ticker1, ticker2)`:
- OLS hedge ratio (log-price regression)
- Rolling 60-day z-score of the cointegrated spread
- Mean-reversion half-life (Ornstein-Uhlenbeck)
- ADF test for spread stationarity (p < 0.05 = mean-reverting)
- Trade signal: LONG / SHORT / NO SIGNAL / EXIT ZONE

## Step 4 — Cointegration test
Call `cointegration_test(ticker1, ticker2)`:
- Engle-Granger test via statsmodels
- p < 0.05 = cointegrated = safe to trade as a pair

## Step 5 — Beta-neutral sizing
Call `beta_neutral_sizing(ticker1, ticker2)`:
- Individual SPY betas, size ratio, net residual beta after hedging

## Step 6 — Relative valuation
Call `relative_valuation(ticker1, ticker2)`:
- Forward P/E, EV/EBITDA, EV/Revenue, P/Book for each leg
- 2Y price ratio z-score as valuation divergence proxy

## Step 7 — IV ratio
Call `iv_ratio_analysis(ticker1, ticker2)`:
- ATM IV for both legs (30-day expiry)
- IV ratio, cheaper options leg, structural implication

## Step 8 — Earnings alignment
Call `earnings_alignment(ticker1, ticker2)`:
- Next earnings date and DTE for each leg
- Gap in days, event risk flag if gap > 14 days

## Step 9 — Output

---

## PAIRS ANALYSIS — {TICKER1} / {TICKER2} — {Date}

| | {TICKER1} | {TICKER2} |
|---|---|---|
| Price | $XX.XX | $XX.XX |
| Beta (vs. SPY) | X.XX | X.XX |
| ATM IV (30d) | XX% | XX% |
| Fwd P/E | XX.Xx | XX.Xx |
| EV/EBITDA | XX.Xx | XX.Xx |

---

### Pair Quality
| Metric | Value | Interpretation |
|---|---|---|
| 90-day correlation | X.XX | [Strong ≥0.70 / Moderate 0.45-0.70 / Weak <0.45] |
| Correlation trend | [Increasing / Stable / Decreasing] | [What this implies] |
| Cointegrated? | [YES / NO] (p=X.XXXX) | [Stable long-run relationship vs. trending apart] |
| Spread stationary? | [YES / NO] (ADF p=X.XXXX) | [Mean-reverting vs. random walk] |
| Mean-reversion half-life | X.X days | [Tradeable: 5-30d / Slow: 30-60d / Not actionable: >60d] |

**Pair quality verdict:** [1-2 sentences — is this a statistically sound pair to trade? What is the primary risk?]

---

### Spread Signal
- **Current z-score:** X.XX (60-day window)
- **Signal:** [LONG SPREAD — long T1, short T2 / SHORT SPREAD — short T1, long T2 / NO SIGNAL — wait for ±2σ / EXIT ZONE — near mean]
- **Hedge ratio:** X.XXXX (units of {TICKER2} per unit of {TICKER1} in log-price space)

**Recent spread (last 5 sessions):**
| Date | Spread | Z-Score |
|---|---|---|
| [Date] | X.XXXX | X.XX |
| ... | | |

---

### Beta-Neutral Sizing
| Sizing Method | {TICKER1} | {TICKER2} | Net Beta |
|---|---|---|---|
| Dollar-neutral | $1.00 long | $1.00 short | ~X.XX |
| **Beta-neutral** | **$1.00 long** | **$X.XX short** | **~0.00** |

- **Recommended ratio:** For every $1.00 long {TICKER1}, short $X.XX in {TICKER2}
- [Reliability flag if beta > 3.0 or unreliable]

---

### Relative Valuation
| Metric | {TICKER1} | {TICKER2} | Spread | Cheaper |
|---|---|---|---|---|
| Forward P/E | XX.Xx | XX.Xx | +XX.Xx | [Ticker] |
| EV/EBITDA | XX.Xx | XX.Xx | +X.Xx | [Ticker] |
| EV/Revenue | X.Xx | X.Xx | +X.Xx | [Ticker] |
| P/Book | XX.Xx | X.Xx | +XX.Xx | [Ticker] |

- **2Y price ratio z-score:** X.XX — [interpretation: which name is historically expensive/cheap vs. the other]
- **Overall cheaper name:** [Ticker] — [cheaper on X of 4 valuation metrics]

---

### IV Ratio — Options Structure
| | {TICKER1} | {TICKER2} |
|---|---|---|
| ATM IV (30d) | XX% | XX% |
| Expiry | [Date] | [Date] |

- **IV ratio:** X.XX ({TICKER1} options are X% [more/less] expensive than {TICKER2})
- **Cheaper options leg:** {TICKER_}
- **Structural implication:** [Which side to buy options on, which side to sell or use spreads]

---

### Earnings Alignment
| | {TICKER1} | {TICKER2} |
|---|---|---|
| Next earnings | [Date or N/A] | [Date or N/A] |
| DTE | X days | X days |

- **Gap between earnings:** X days
- **Event risk flag:** [YES — consider sizing down / NO — risk well-matched]
- [Note on which leg reports first and the unhedged window if applicable]

---

### Trade Structure Recommendation
[Synthesize all sections into 4-6 bullets:]

- **Pair quality:** [Cointegrated / not cointegrated — tradeable or pass?]
- **Entry signal:** [Current z-score and what level to enter/wait for]
- **Sizing:** [Beta-neutral ratio — $X.XX short per $1.00 long]
- **Direction:** [Which leg long, which short — supported by both spread signal and valuation]
- **Options structure:** [Specific recommendation: e.g., "Buy 30-45 DTE calls on {cheaper IV leg}, sell OTM call spread on {dearer IV leg} — IV ratio X.Xx favors buying vol on {cheaper leg}"]
- **Key risk:** [Correlation breakdown / binary event gap / cointegration failure / other]
