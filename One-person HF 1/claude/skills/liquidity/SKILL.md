---
name: liquidity
description: US and global liquidity analysis. Tracks Fed balance sheet, QT/QE pace, Treasury General Account (TGA), Reverse Repo (RRP), bank reserves, M2 money supply, credit growth, and dollar conditions. Supplements with ECB/BOJ/PBOC balance sheets and cross-border capital flows. Outputs Net Fed Liquidity level and 4-week impulse, a liquidity tightening/easing score (-10 to +10), and explicit risk asset tailwinds/headwinds. Usage: /liquidity
when_to_use: Run weekly or after key Fed/Treasury events (FOMC, Treasury refunding announcements, QT pace changes) to understand the mechanical liquidity backdrop driving asset prices. Use to confirm or challenge fundamental and macro theses with the plumbing-level view.
---

## Step 1 — Local data pull (yfinance market proxies + FRED attempt)

Run the local Python module. It will always return market proxies and will attempt FRED series (may fail on restricted networks):

```bash
cd "c:\Users\uproa\Desktop\One-person HF 1" && python -c "
import sys, json, numpy as np
sys.path.insert(0, 'src/data')
from liquidity import run_full_liquidity_assessment

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.floating, np.integer)): return float(obj)
        return super().default(obj)

result = run_full_liquidity_assessment()
print(json.dumps(result, indent=2, cls=NpEncoder))
"
```

Note which FRED series returned `available: false`. Those need to be fetched in Step 2.

---

## Step 2 — Fetch unavailable FRED series via WebFetch

For each FRED series that returned `available: false` in Step 1, use WebFetch on the public CSV endpoint (no API key required — goes through Claude's network, not local):

| Series | URL | Unit | Notes |
|---|---|---|---|
| WALCL (Fed BS) | https://fred.stlouisfed.org/graph/fredgraph.csv?id=WALCL | $B | Weekly, Wed |
| WTREGEN (TGA) | https://fred.stlouisfed.org/graph/fredgraph.csv?id=WTREGEN | $M → ÷1000=$B | Weekly, Wed |
| RRPONTSYD (RRP) | https://fred.stlouisfed.org/graph/fredgraph.csv?id=RRPONTSYD | $B | Daily |
| WRESBAL (Reserves) | https://fred.stlouisfed.org/graph/fredgraph.csv?id=WRESBAL | $B | Weekly, Wed |
| M2SL (M2) | https://fred.stlouisfed.org/graph/fredgraph.csv?id=M2SL | $B | Monthly |
| TOTLL (Total Loans) | https://fred.stlouisfed.org/graph/fredgraph.csv?id=TOTLL | $B | Weekly |

For each WebFetch: prompt = "Extract the last 15 rows of data as a table of date and value. Report the most recent value, the value 4 weeks ago, the value 13 weeks ago, and the value 52 weeks ago."

From these compute:
- **4-week change** = latest − value 4 weeks ago
- **13-week change** = latest − value 13 weeks ago
- **YoY change %** = (latest − value 52 weeks ago) / value 52 weeks ago × 100

---

## Step 3 — Global central bank balance sheets (WebSearch)

Search for the most recent available readings. Convert all to USD billions using current FX rates from the market proxies (EURUSD, USDJPY, USDCNY).

**ECB:**
- WebSearch: "ECB balance sheet total assets EUR billions [current month year]"
- Or WebFetch: https://fred.stlouisfed.org/graph/fredgraph.csv?id=ECBASSETS (millions EUR → ÷1000 for billions)
- Convert to USD: EUR billions × EURUSD rate
- Compute 4w and 13w change in USD equivalent

**Bank of Japan (BOJ):**
- WebSearch: "Bank of Japan balance sheet total assets JPY trillions [current month year]"
- Convert to USD: JPY trillions × 1000 ÷ USDJPY rate
- Compute 4w and 13w change in USD equivalent

**PBOC (People's Bank of China):**
- WebSearch: "PBOC total assets CNY trillions [current month year]"
- Convert to USD: CNY trillions × 1000 ÷ USDCNY rate (use 7.25 if rate unavailable)
- Compute 4w and 13w change in USD equivalent

**Global Central Bank Liquidity (USD):**
- Sum of Fed BS + ECB (USD) + BOJ (USD) + PBOC (USD)
- 4w and 13w change in this aggregate

---

## Step 4 — Cross-border capital flows and dollar liquidity (WebSearch)

Search for the most recent available data:

1. **TIC Data (Treasury International Capital):** "US Treasury TIC data net foreign purchases [recent month year]" — Look for foreign official and private purchases of US Treasuries. Rising foreign demand = dollar inflow / dollar strength signal.

2. **Fed FX Swap Lines:** "Federal Reserve swap line usage [current month year]" — Elevated swap line usage = dollar funding stress in foreign markets (tightening signal).

3. **Eurodollar / cross-currency basis:** "USD cross-currency basis swap EUR JPY [current]" — If basis is deeply negative, offshore dollar funding is expensive → tightening global dollar liquidity.

4. **US Dollar Funding Conditions:** WebSearch "repo rate SOFR spread [current]" — SOFR well above Fed funds = repo market stress.

If specific data is unavailable, note that and use the DXY trend (from market proxies) as the primary dollar liquidity proxy.

---

## Step 5 — QT/QE Pace Analysis

From the Fed BS data (WALCL), compute:
- **Stated QT pace:** (WebSearch "Fed QT quantitative tightening pace current" to confirm current announced runoff cap for Treasuries and MBS)
- **Actual 4-week pace:** WALCL 4-week change ÷ 4 weeks = actual weekly runoff rate × 4 = monthly pace in $B
- **Variance:** Actual vs. stated QT pace — if balance sheet is shrinking faster than announced, QT is running hot; if slower, QT may be pausing/slowing (more stimulative than expected)
- **QT/QE label:** If 4w change is positive → net easing (QE or reinvestment); negative → net tightening (QT)

---

## Step 6 — Compute scores and synthesize

Using all data from Steps 1–5, run the scoring function from the module OR compute manually using these thresholds:

### Net Fed Liquidity (NFL)
**NFL = Fed BS − TGA − RRP** (all in $B)
- NFL 4-week impulse = NFL_now − NFL_4w_ago
- Positive impulse → net easing; negative → net tightening
- The NFL impulse has high historical correlation (~0.85) with S&P 500 direction over 4–13 week periods

### Liquidity Score: 8 Components (-2 to +2 each = -16 to +16 raw, normalized to -10 to +10)

| # | Component | Tightening (-2/-1) | Neutral (0) | Easing (+1/+2) |
|---|---|---|---|---|
| 1 | Fed BS 4w change | < -$50B / -$50 to -$10B | ±$10B | +$10-50B / >+$50B |
| 2 | TGA 4w change (inv.) | TGA rose >$100B / $50-100B | ±$50B | TGA fell $50-100B / >$100B |
| 3 | RRP 4w change (inv.) | RRP rose >$100B / $50-100B | ±$50B | RRP fell $50-100B / >$100B |
| 4 | Bank Reserves level | < $2.0T / $2.0-2.5T | $2.5-3.0T | $3.0-3.5T / >$3.5T |
| 5 | M2 YoY growth | < -2% / -2 to 0% | 0-4% | 4-8% / >8% |
| 6 | DXY 4w change (inv.) | DXY +3%+ / +1-3% | ±1% | DXY -1 to -3% / <-3% |
| 7 | Credit (Total Loans) YoY | < 0% / 0-3% | 3-6% | 6-10% / >10% |
| 8 | NFL impulse 4w | < -$100B / -$100 to -$25B | ±$25B | +$25-100B / >+$100B |

**Score interpretation:**
| Score | Regime | Risk Asset Implication |
|---|---|---|
| +6 to +10 | **STRONG EASING** | Significant tailwind — liquidity expansion is a primary price driver |
| +2 to +5 | **MODERATE EASING** | Mild tailwind — supportive but not the dominant driver |
| -1 to +1 | **NEUTRAL** | Liquidity neither headwind nor tailwind — fundamentals drive |
| -2 to -5 | **MODERATE TIGHTENING** | Mild headwind — risk assets face moderate mechanical pressure |
| -6 to -10 | **STRONG TIGHTENING** | Significant headwind — liquidity contraction is mechanically suppressing prices |

---

## Step 7 — Save report

Save the full report to: `reports/liquidity-{YYYY-MM-DD}.md`

---

## Step 8 — Output format

---

## LIQUIDITY ASSESSMENT — {today's date}

### Net Liquidity Score: X.X / 10
**Regime: [STRONG EASING / MODERATE EASING / NEUTRAL / MODERATE TIGHTENING / STRONG TIGHTENING]**

> [One sentence: the single most important liquidity driver right now]

---

### Net Fed Liquidity
| Metric | Value | Signal |
|---|---|---|
| Fed Balance Sheet | $X,XXX.XB | [Rising/Falling at $XXB/month] |
| Treasury General Account (TGA) | $XXX.XB | [Draining/Building — [easing/tightening]] |
| Reverse Repo (RRP) | $XX.XB | [Declining/Rising — [releasing/absorbing] reserves] |
| **Net Fed Liquidity (Fed BS − TGA − RRP)** | **$X,XXX.XB** | — |
| NFL 4-week impulse | [+/-$XXB] | [Easing / Tightening] |
| NFL 13-week impulse | [+/-$XXB] | [Easing / Tightening] |

**NFL interpretation:** [2-3 sentences: is liquidity expanding or contracting mechanically? What is driving it — balance sheet, TGA dynamics, or RRP? What does this imply for the next 4-8 weeks?]

---

### QT/QE Pace
- **Current Fed policy:** [QT / QE / Neutral]
- **Announced pace:** $XXB/month (Treasuries: $XXB | MBS: $XXB)
- **Actual 4-week pace:** $XXB/month (actual balance sheet change)
- **Variance:** [Running [faster/slower/in line] than announced by $XXB/month]
- **Signal:** [Hot QT — more restrictive than expected / QT slowing — less restrictive than expected / QE — actively stimulative]

---

### Fed Balance Sheet Detail
- **Current total:** $X,XXX.XB | **4w change:** [+/-$XXB] | **13w change:** [+/-$XXB] | **YoY:** [+/-X%]
- **Peak (Apr 2022):** ~$8,965B | **Reduction to date:** ~$X,XXXB (-XX% from peak)
- **Composition shift:** [Note if Treasury vs. MBS runoff is dominating]

---

### Treasury General Account (TGA)
- **Current:** $XXX.XB | **4w change:** [+/-$XXB] | **13w change:** [+/-$XXB]
- **Context:** [Is Treasury building reserves ahead of debt ceiling / spending down after issuance? Low TGA = Treasury spending into the economy = reserve-additive = easing]
- **Debt ceiling / refunding note:** [Any near-term TGA dynamics from Treasury refunding announcements or debt ceiling constraints]

---

### Reverse Repo Facility (RRP)
- **Current:** $XX.XB | **4w change:** [+/-$XXB] | **Peak (Dec 2022):** ~$2,554B
- **Drain rate:** [At current pace, RRP depleted in ~X months / already near zero]
- **Signal:** [Declining RRP → cash being deployed into T-bills/markets (stimulative) / Rising RRP → cash retreating to Fed (restrictive)]
- **Near-zero risk:** [If RRP is near zero, this liquidity release mechanism is exhausted — flag if so]

---

### Bank Reserves
- **Current:** $X,XXX.XB | **4w change:** [+/-$XXB]
- **Minimum comfortable level (MCLoR):** est. ~$2,500–3,000B
- **Buffer above MCLoR:** [+/-$XXXB — [ample/tight/stressed]]
- **Repo market signal:** [SOFR vs. Fed funds rate spread — any repo stress?]
- **Note:** When reserves approach MCLoR, repo market stress emerges (as in Sept 2019). Current buffer provides [X months] of runway at current QT pace.

---

### Money Supply (M2)
- **Current:** $XX,XXX.XB | **YoY change:** [+/-X%] | **4w change:** [+/-$XXB]
- **Real M2 (deflated by CPI):** [growing/contracting at X% YoY]
- **Historical context:** M2 growth >5% YoY historically associated with asset price inflation; M2 contraction historically associated with deflationary pressure on asset prices
- **Signal:** [🟢 Expansionary / 🟡 Neutral / 🔴 Contractionary]

---

### Credit Growth
- **Total Loans & Leases (commercial banks):** $XX,XXX.XB | **YoY:** [+/-X%]
- **4w change:** [+/-$XXB]
- **Credit impulse:** [Accelerating / Stable / Decelerating] — [private sector credit creation is [amplifying/offsetting] Fed liquidity dynamics]
- **Signal:** [🟢 Credit expanding — private liquidity amplifier / 🟡 Neutral / 🔴 Credit contracting — private liquidity drag]

---

### Dollar Liquidity
| Metric | Value | 4w Change | Signal |
|---|---|---|---|
| DXY (Dollar Index) | XX.XX | [+/-X%] | [Tighter/Easier global dollar conditions] |
| Gold | $X,XXX | [+/-X%] | [Real liquidity / inflation hedge demand] |
| Copper | $X.XX/lb | [+/-X%] | [Global industrial demand / growth proxy] |
| Bitcoin | $XX,XXX | [+/-X%] | [Risk / liquidity barometer] |
| EURUSD | X.XXXX | [+/-X%] | [Dollar strength direction] |

- **Dollar trend:** [DXY [rising/falling] — tightening/easing global USD funding conditions]
- **Cross-currency basis:** [If data available: tight/wide — offshore dollar funding stress]
- **Fed swap line usage:** [If elevated: dollar funding stress offshore]
- **Dollar liquidity signal:** [🟢 Dollar weakening — easing global conditions / 🟡 Stable / 🔴 Dollar strengthening — tightening global conditions]

---

### Global Central Bank Liquidity
| Central Bank | Balance Sheet | Currency | USD Equivalent | 4w Change (USD) |
|---|---|---|---|---|
| Federal Reserve | $X,XXX.XB | USD | $X,XXX.XB | [+/-$XXB] |
| ECB | €X,XXX.XB | EUR | $X,XXX.XB | [+/-$XXB] |
| Bank of Japan | ¥XXX.XT | JPY | $X,XXX.XB | [+/-$XXB] |
| PBOC | ¥XX.XT | CNY | $X,XXX.XB | [+/-$XXB] |
| **Global Total** | — | — | **$XX,XXX.XB** | **[+/-$XXB]** |

- **Global CB impulse (4w):** [+/-$XXXB — expanding/contracting]
- **Global CB impulse (13w):** [+/-$XXXB — expanding/contracting]
- **Key driver:** [Which CB is the dominant mover? Fed? ECB (defense spending QE)? BOJ (YCC adjustment)?]
- **Global CB signal:** [🟢 Expanding in aggregate / 🟡 Diverging — some easing, some tightening / 🔴 Contracting in aggregate]

---

### Cross-Border Capital Flows
- **TIC Data (most recent):** [Foreign net purchases of US securities — $XXB in [month]. Foreign demand for US assets [rising/falling]]
- **Foreign official holdings of Treasuries:** [Rising/Falling — dollar reserve recycling trend]
- **EM capital flow:** [If DXY falling + EM equities rising (EEM +X% 4w), capital is flowing to EM — dollar-funding conditions easing]
- **Signal:** [Inflows supporting USD assets / Outflows from USD assets]

---

### Liquidity Score Breakdown
| Component | Current Value | 4w Change | Score | Weight |
|---|---|---|---|---|
| 1. Fed Balance Sheet | $X,XXX.XB | [+/-$XXB] | [+/-X] | / 2 |
| 2. TGA (inverted) | $XXX.XB | [+/-$XXB] | [+/-X] | / 2 |
| 3. RRP (inverted) | $XX.XB | [+/-$XXB] | [+/-X] | / 2 |
| 4. Bank Reserves level | $X,XXX.XB | [+/-$XXB] | [+/-X] | / 2 |
| 5. M2 YoY growth | [+/-X%] | — | [+/-X] | / 2 |
| 6. DXY (inverted) | XX.XX | [+/-X% 4w] | [+/-X] | / 2 |
| 7. Credit growth YoY | [+/-X%] | — | [+/-X] | / 2 |
| 8. NFL impulse 4w | [+/-$XXB] | — | [+/-X] | / 2 |
| **TOTAL** | — | — | **X.X / 10** | |

---

### Risk Asset Tailwinds / Headwinds

**Net liquidity impulse for risk assets:** [TAILWIND / HEADWIND / NEUTRAL]

**Equities (SPX, NDX):**
- [1-2 sentences: does current liquidity regime support or suppress equity multiples? Is the NFL impulse expanding or contracting? Historical: NFL impulse >+$100B/month = strong tailwind for equities; NFL impulse <-$100B = strong headwind]
- **Near-term (4-week) signal:** [🟢 Tailwind / 🟡 Neutral / 🔴 Headwind]
- **Medium-term (13-week) signal:** [🟢 Tailwind / 🟡 Neutral / 🔴 Headwind]

**Credit markets (HYG, LQD):**
- [1 sentence: credit tends to tighten before equities — is HYG credit spread signaling stress ahead of equities?]
- **HYG 4w performance:** [+/-X%] | **LQD 4w performance:** [+/-X%]
- **Signal:** [Spreads tightening (bullish) / widening (bearish)]

**Emerging markets (EEM, EM FX):**
- [1 sentence: EM assets are highly sensitive to dollar direction — DXY falling = EM tailwind, DXY rising = EM headwind]
- **EEM 4w:** [+/-X%] | **Dollar direction:** [Easing/Tightening]
- **Signal:** [🟢 Dollar easing → EM tailwind / 🔴 Dollar tightening → EM headwind]

**Commodities (Gold, Copper, Oil):**
- [1 sentence: gold benefits from loose liquidity + weak dollar; copper reflects industrial demand, not just liquidity]
- **Gold 4w:** [+/-X%] | **Copper 4w:** [+/-X%]
- **Signal:** [Liquidity [supportive/neutral/restrictive] for commodities]

**Bitcoin / Crypto:**
- [1 sentence: BTC has historically tracked NFL with ~4-week lag; current BTC move vs. NFL impulse]
- **BTC 4w:** [+/-X%] | **NFL impulse 4w:** [+/-$XXB]
- **Signal:** [Confirming / Diverging — divergence often resolves toward NFL direction]

---

### Synthesis: What Is Driving Asset Prices Right Now?

**Mechanical driver assessment:**
[2-3 sentences: is the current market environment primarily liquidity-driven, earnings-driven, or sentiment-driven? If NFL impulse is large (>±$100B/4w), liquidity is the dominant driver. If NFL is neutral, fundamentals matter more. If liquidity and fundamentals diverge, flag the tension.]

**Key risks to the liquidity backdrop:**
- [Risk 1: e.g., TGA rebuild after debt ceiling resolution would drain reserves]
- [Risk 2: e.g., Fed accelerating QT if inflation re-accelerates]
- [Risk 3: e.g., RRP near zero — the liquidity release buffer is exhausted, removing a tailwind]

**Key potential catalysts for liquidity improvement:**
- [Catalyst 1: e.g., Debt ceiling breach / resolution forcing Treasury spending down → TGA drain]
- [Catalyst 2: e.g., Fed pausing QT — balance sheet stabilization]
- [Catalyst 3: e.g., Global CB coordination — ECB or BOJ expanding balance sheets]

**Portfolio implication:**
[2-3 sentences: given the liquidity score of X.X, what is the mechanical setup for risk assets over the next 4-8 weeks? Should the portfolio be positioned more offensively (high liquidity score) or defensively (low score)? Any specific rotation implied (EM vs. US, growth vs. value, credit vs. equity)?]
