---
name: flow
description: Options flow analysis for a ticker. Pulls put/call volume and OI ratios, max pain, OI distribution by strike (call walls / put walls), and unusual options activity. Usage: /flow [TICKER]
when_to_use: Use after /vol to complete the options picture before structuring a trade. Run when you want to know where market makers are positioned, where smart money is active, and what key strike levels will act as support/resistance.
---

The user will provide a ticker symbol. Use `src/data/options_flow.py` to run the full flow analysis via `full_flow_analysis(ticker)`. Also pull the ATM strike and current price from yfinance for context.

## Step 1 — Put/Call Ratios
Call `put_call_ratios(ticker)`:
- Aggregate call and put volume and open interest across the nearest 4 expiries
- P/C Volume ratio: >1.2 = bearish lean; <0.7 = bullish lean
- P/C OI ratio: baseline positioning (slower-moving than volume)

## Step 2 — Max Pain
Call `max_pain(ticker)` for the expiry closest to 30 days:
- Identifies the strike where total option buyer intrinsic value is minimized
- Price gravitates toward max pain into expiration due to MM delta hedging
- Note distance from current price and directional implication

## Step 3 — OI Distribution (Call Wall / Put Wall)
Call `oi_distribution(ticker)` for the 30-day expiry:
- Top 10 strikes by OI for calls and puts
- **Call wall**: highest OI call above current price → gamma resistance level
- **Put wall**: highest OI put below current price → gamma support level
- These levels act as magnets or barriers depending on GEX regime

## Step 4 — Unusual Options Activity (UOA)
Call `unusual_options_activity(ticker)`:
- Scans first 5 expiries for volume/OI ratio ≥ 2.5x with minimum 200 contracts
- High vol/OI = fresh positioning (not existing hedges rolling)
- Flag ITM vs. OTM, DTE, and size — large OTM with short DTE is most significant
- Note direction (calls vs. puts) and whether activity is clustered at a specific strike

## Step 5 — Output

---

## OPTIONS FLOW — {TICKER} — {Date}

**Current Price:** $XX.XX

### Put/Call Ratios
| Metric | Value | Signal |
|---|---|---|
| P/C Volume Ratio | X.XX | [Bearish lean / Neutral / Bullish lean] |
| P/C OI Ratio | X.XX | [Description] |
| Total Call Volume | XXX,XXX | — |
| Total Put Volume | XXX,XXX | — |
| Total Call OI | XXX,XXX | — |
| Total Put OI | XXX,XXX | — |

**Sentiment:** [What the ratios indicate about near-term directional positioning]

---

### Max Pain
- **Max Pain Strike:** $XX.XX ([expiry date])
- **Distance from current price:** [+X% above / -X% below current price]
- **Implication:** [If price is above max pain, MMs are long delta above it and will hedge by selling into strength toward that level. If below, they buy weakness. Interpret directional pull and how close to expiry this matters.]

---

### OI Distribution — Key Levels

**Call Wall (resistance):** $XX.XX — [X,XXX contracts]
**Put Wall (support):** $XX.XX — [X,XXX contracts]

**Top Call Strikes by OI**
| Strike | Open Interest | IV | vs. Price |
|---|---|---|---|
| $XX.XX | X,XXX | XX% | +X% OTM |
| ... | | | |

**Top Put Strikes by OI**
| Strike | Open Interest | IV | vs. Price |
|---|---|---|---|
| $XX.XX | X,XXX | XX% | -X% OTM |
| ... | | | |

**Key level interpretation:** [What the call wall and put wall imply for near-term price action. Is there a gamma pin zone? Is the stock likely to be repelled from or attracted to these levels?]

---

### Unusual Options Activity (UOA)

[If no unusual activity: "No significant unusual options activity detected across the scanned expiries."]

| Expiry | DTE | Type | Strike | Moneyness | Volume | OI | Vol/OI | IV | Last |
|---|---|---|---|---|---|---|---|---|---|
| [Date] | X | Call/Put | $XX.XX | +X% OTM | X,XXX | X,XXX | X.Xx | XX% | $X.XX |
| ... | | | | | | | | | |

**UOA interpretation:**
- [Bullet per notable cluster: what type, at what strike, what DTE, and what it suggests about smart money positioning]
- [Flag if activity is consistent with a directional bet, a hedge, or an earnings play]
- [Note if UOA aligns or conflicts with your directional thesis]

---

### Synthesis — Trade Structuring Inputs
[3-5 bullet points connecting all flow data to actionable options structure guidance:]
- **Key levels to respect:** Call wall at $X (resistance), put wall at $X (support), max pain at $X
- **MM positioning:** [Are MMs likely to dampen or amplify moves based on where OI is concentrated?]
- **Smart money signal:** [Does UOA confirm or contradict the directional thesis?]
- **Strike selection:** [Where should you target based on call/put walls and max pain?]
- **P/C sentiment vs. price action:** [Is the options market aligned with the tape, or diverging?]

**Recommended next step:** Run `/vol {TICKER}` for IV rank, skew, and term structure before finalizing trade structure.
