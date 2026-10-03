---
name: growth
description: US economic growth assessment. Analyzes ISM Manufacturing and Services PMIs, University of Michigan Consumer Sentiment, Building Permits, Non-Farm Payrolls, Durable Goods Orders, and Industrial Production against growth thresholds. Confirms each major indicator with earnings signals from relevant sector companies (transportation, defense, raw materials, consumer goods). Outputs a structured growth regime verdict. Usage: /growth
when_to_use: Run after major economic data releases (ISM, NFP, Durable Goods, Industrial Production) to assess whether the US economy is in expansion or contraction, and whether sector-level earnings are confirming or diverging from the macro picture.
---

Run the **Macro Researcher** agent and a **general-purpose** agent in parallel. Then synthesize both outputs into the structured growth report below.

---

## AGENT 1 — Macro Researcher

Pull and interpret all 6 economic indicators. For each indicator:
- Report the most recent print and the prior print
- Compare to the growth threshold benchmarks defined below
- Give a one-sentence interpretation

**Data sources (in order of priority):**
1. Alpha Vantage economic indicator API (for NFP and Durable Goods): use `function=NONFARM_PAYROLL` and `function=DURABLES`
2. WebSearch for the most recent readings of ISM Manufacturing PMI, ISM Services PMI, University of Michigan Consumer Sentiment, Building Permits, and Industrial Production / Capacity Utilization
3. If a specific release is not yet available (just released today), search for the advance estimate

**Indicators to pull:**

### Indicator 1 — ISM Manufacturing PMI
- Source: Institute for Supply Management (ISM), released first business day of each month
- Most recent reading vs. prior month vs. 12-month average
- **Growth thresholds:**
  | Reading | Regime |
  |---|---|
  | < 46 | Hard contraction |
  | 46–50 | Contraction |
  | 50–52 | Borderline expansion |
  | 52–55 | Healthy expansion |
  | > 55 | Strong expansion |
- Sub-components to note if available: New Orders, Production, Employment, Supplier Deliveries, Inventories
- **Growth benchmark:** 52.0 is the minimum for sustained economic growth; readings >50 but <52 signal fragile expansion

### Indicator 2 — ISM Services PMI
- Source: Institute for Supply Management, released 3rd business day of each month
- Most recent reading vs. prior month vs. 12-month average
- **Growth thresholds:** Same scale as Manufacturing (50 = expansion threshold, 52+ = healthy)
- Services PMI is more heavily weighted to current economic activity (~70% of US GDP)
- **Growth benchmark:** 52.0+. Services below 50 is a strong recession signal given GDP composition

### Indicator 3 — University of Michigan Consumer Sentiment (UCSMCI)
- Source: University of Michigan, released second Friday of each month (preliminary) / last Friday (final)
- Report preliminary and final readings if both available
- **Growth thresholds:**
  | Reading | Regime |
  |---|---|
  | < 65 | Recession-level pessimism |
  | 65–75 | Weak consumer confidence |
  | 75–90 | Moderate — long-run average zone |
  | 90–100 | Strong consumer confidence |
  | > 100 | Exceptional |
- **Long-run average:** ~86 (1978–present). Readings below 75 historically precede consumption slowdowns
- Note the 1-year and 5-year inflation expectations components if available — key for Fed policy

### Indicator 4 — Monthly Building Permits (SAAR)
- Source: US Census Bureau / HUD, released ~3rd week of each month
- Report total, single-family, and multi-family permits in millions (SAAR) if available
- **Growth thresholds:**
  | Total Permits (SAAR, M) | Regime |
  |---|---|
  | < 1.20M | Weak — housing in contraction |
  | 1.20–1.40M | Below trend |
  | 1.40–1.60M | Near trend — moderate growth |
  | 1.60–1.80M | Healthy |
  | > 1.80M | Strong expansion |
- **Growth benchmark:** 1.50M permits SAAR = breakeven for housing's contribution to GDP growth. Single-family permits >900K = healthy residential investment.
- Housing leads the economic cycle by 6–12 months — declining permits signal future construction weakness

### Indicator 5 — Non-Farm Payrolls (NFP) / Employment Situation
- Source: Bureau of Labor Statistics, released first Friday of each month
- Report: headline NFP (jobs added), unemployment rate, average hourly earnings (MoM and YoY), labor force participation rate
- **Growth thresholds:**
  | NFP Monthly (K) | Regime |
  |---|---|
  | < 50 | Contraction risk |
  | 50–125 | Below trend — slowing |
  | 125–200 | Trend growth — sufficient |
  | 200–300 | Above trend — strong |
  | > 300 | Very strong / possibly overheating |
- **Growth benchmark:** 125–150K/month = the minimum consistent with stable unemployment given labor force growth. Below this for 2+ months signals labor market softening.
- Also note private vs. government job splits; manufacturing and construction payrolls as cyclical leading indicators

### Indicator 6 — US Durable Goods Orders and Shipments
- Source: US Census Bureau, released ~4th week of each month
- Report: headline new orders MoM%, core capital goods orders (ex-defense, ex-aircraft) MoM%, and shipments MoM%
- **Growth thresholds for Core Capital Goods Orders (ex-defense, ex-aircraft):**
  | MoM Change | Signal |
  |---|---|
  | < -1.0% | Business investment contracting |
  | -1.0% to 0% | Slowing — watch for trend |
  | 0–0.5% | Neutral |
  | 0.5–1.0% | Healthy business investment |
  | > 1.0% | Strong capex momentum |
- **Growth benchmark:** Core capital goods orders running flat to +0.5% MoM on a 3-month average = minimum for sustained business investment. Headline orders are volatile due to aircraft — always focus on the core.
- Report YoY change in shipments as a growth rate for industrial activity

### Indicator 7 — US Industrial Production and Capacity Utilization
- Source: Federal Reserve, released ~2nd week of each month
- Report: Industrial Production Index MoM% and YoY%, Manufacturing output MoM%, and Capacity Utilization %
- **Growth thresholds:**
  | Capacity Utilization | Regime |
  |---|---|
  | < 74% | Significant slack — recessionary |
  | 74–78% | Below trend |
  | 78–82% | Healthy — near optimal |
  | > 82% | Tight — inflationary pressure risk |
- **Industrial Production YoY growth benchmark:** +2.0% YoY = minimum for expansion. Negative YoY for 2+ months = industrial recession.
- Note manufacturing vs. utilities vs. mining sub-components

---

## AGENT 2 — General Purpose (Company Earnings Confirmation)

Pull the most recent quarterly earnings data for all 9 companies below using yfinance (`sys.path.insert(0, 'src/data')` is available; also use WebSearch for any earnings released in the past 30 days not yet in yfinance).

Run yfinance for each company: `yf.Ticker(ticker).quarterly_income_stmt`, `.info`, and news via `src/data/news_client.py`.

### Group A — Durable Goods Confirmation

**Transportation (confirm goods movement / supply chain activity):**

| Ticker | Company | Key Signal to Extract |
|---|---|---|
| BA | Boeing | Commercial aircraft deliveries (units), defense segment revenue, order backlog |
| UNP | Union Pacific | Total carloadings (units YoY%), revenue per car, operating ratio |
| FDX | FedEx | Package volume YoY%, revenue per package, guidance tone |

**Defense (confirm government durable goods spending):**

| Ticker | Company | Key Signal to Extract |
|---|---|---|
| LMT | Lockheed Martin | Total revenue YoY%, backlog, segment trends (Aeronautics, Missiles & Fire Control) |
| RTX | Raytheon Technologies | Defense segment revenue, order intake, commercial aerospace split |
| NOC | Northrop Grumman | Revenue YoY%, backlog growth, B2 bomber / space segment trends |

**Signal interpretation:**
- Rising carloadings (UNP) + rising FedEx volumes = goods demand is growing → **confirms** durable goods strength
- Declining shipments / falling operating ratios = goods movement slowing → **conflicts** with strong durable goods prints
- Growing defense backlogs (LMT, RTX, NOC) = government capex supporting headline durable goods → **explains** defense-driven spikes in headline number

### Group B — Industrial Production Confirmation

**Raw Materials (confirm industrial input demand):**

| Ticker | Company | Key Signal to Extract |
|---|---|---|
| MT | ArcelorMittal | Steel shipments (million tons), realized steel price per ton, guidance |
| AA | Alcoa | Aluminum shipments (K mt), realized price, guidance |
| DOW | Dow Inc | Volume YoY%, pricing YoY%, segment demand commentary |

**Consumer Goods (confirm production levels and end-demand):**

| Ticker | Company | Key Signal to Extract |
|---|---|---|
| PG | Procter & Gamble | Organic revenue growth, volume vs. price split, market share |
| UL | Unilever | Underlying volume growth, pricing, geographic commentary |
| KO | Coca-Cola | Unit case volume YoY%, pricing, channel mix |

**Signal interpretation:**
- Growing steel/aluminum shipments (MT, AA) = industrial production is running → **confirms** IP strength
- Falling raw material volumes + inventory builds = production is slowing → **conflicts** with healthy IP prints
- Positive PG/KO/UL volumes = consumer goods production is elevated → **confirms** consumer demand holding

For each company, report:
- Most recent quarter revenue ($B) and YoY growth %
- The ONE key physical volume metric (carloadings, tons, cases, units)
- Whether revenue/volume beat or missed consensus
- One-sentence management commentary on demand outlook

---

## SYNTHESIS — Growth Regime Assessment

After both agents complete, synthesize their output into this structured report:

---

## US GROWTH ASSESSMENT — {today's date}

### Growth Scorecard
| Indicator | Latest Print | Prior | Benchmark | vs. Benchmark | Signal |
|---|---|---|---|---|---|
| ISM Manufacturing PMI | XX.X | XX.X | 52.0 | [Above / Below] | [🟢 / 🟡 / 🔴] |
| ISM Services PMI | XX.X | XX.X | 52.0 | [Above / Below] | [🟢 / 🟡 / 🔴] |
| UMich Consumer Sentiment | XXX | XXX | 86 (LR avg) | [Above / Below] | [🟢 / 🟡 / 🔴] |
| Building Permits (SAAR) | X.XXM | X.XXM | 1.50M | [Above / Below] | [🟢 / 🟡 / 🔴] |
| Non-Farm Payrolls | +XXXk | +XXXk | 125–150k | [Above / At / Below] | [🟢 / 🟡 / 🔴] |
| Durable Goods (Core MoM) | +X.X% | +X.X% | Flat to +0.5% | [Above / At / Below] | [🟢 / 🟡 / 🔴] |
| Industrial Production (YoY) | +X.X% | +X.X% | +2.0% | [Above / Below] | [🟢 / 🟡 / 🔴] |
| Capacity Utilization | XX.X% | XX.X% | 78–82% | [In range / Below / Above] | [🟢 / 🟡 / 🔴] |

**Signal key:** 🟢 = Above growth threshold | 🟡 = Borderline / watch | 🔴 = Below threshold

**Score: X/8 indicators above growth threshold**

---

### Growth Regime Verdict
**[EXPANSION / BORDERLINE EXPANSION / SLOWING / CONTRACTION]**

[2-3 sentences: what is the overall growth picture? Which indicators are the most important divergences? Is the data consistent or are there contradictions between sectors?]

---

### Indicator Deep Dive

#### 1. ISM Manufacturing PMI — [Reading] ([Signal])
- **Latest:** XX.X | **Prior:** XX.X | **12-month avg:** XX.X | **Benchmark:** 52.0
- **Sub-components:** New Orders: XX.X | Production: XX.X | Employment: XX.X | Inventories: XX.X
- **Interpretation:** [1-2 sentences on what the reading implies for manufacturing activity and direction of travel]
- **Trend:** [Improving / Deteriorating / Stable] — [X consecutive months above/below 50]

#### 2. ISM Services PMI — [Reading] ([Signal])
- **Latest:** XX.X | **Prior:** XX.X | **12-month avg:** XX.X | **Benchmark:** 52.0
- **Interpretation:** [1-2 sentences — emphasize that Services drives ~70% of US GDP]
- **Trend:** [Improving / Deteriorating / Stable]

#### 3. UMich Consumer Sentiment — [Reading] ([Signal])
- **Latest:** XXX | **Prior:** XXX | **Long-run avg:** ~86 | **Benchmark:** 75 (floor)
- **1-year inflation expectations:** X.X% | **5-year inflation expectations:** X.X%
- **Interpretation:** [1-2 sentences on consumer confidence and any inflation expectation signals for Fed policy]

#### 4. Building Permits — [X.XXM SAAR] ([Signal])
- **Latest:** X.XXM SAAR | **Prior:** X.XXM | **Benchmark:** 1.50M
- **Single-family:** X.XXM | **Multi-family:** X.XXM (if available)
- **Interpretation:** [1-2 sentences — note lead time of 6-12 months for housing's GDP impact]

#### 5. Non-Farm Payrolls — [+XXXk] ([Signal])
- **NFP:** +XXXk | **Prior (revised):** +XXXk | **Benchmark:** 125–150k
- **Unemployment rate:** X.X% | **Avg hourly earnings:** +X.X% YoY | **Labor force participation:** XX.X%
- **Private vs. government split:** Private: +XXXk | Government: +XXk
- **Interpretation:** [1-2 sentences on labor market strength and wage growth implications for Fed policy]

#### 6. Durable Goods Orders — [Signal]
- **Headline orders MoM:** +X.X% | **Core capital goods (ex-def, ex-aircraft) MoM:** +X.X% | **Benchmark:** +0.5%
- **Core shipments MoM:** +X.X% (more signal than orders — orders lead, shipments confirm)
- **3-month average core orders:** +X.X%
- **Interpretation:** [1-2 sentences — note whether headline is distorted by aircraft/defense; focus on core]

#### 7. Industrial Production / Capacity Utilization — [Signal]
- **Industrial Production MoM:** +X.X% | **YoY:** +X.X% | **Benchmark:** +2.0% YoY
- **Manufacturing output MoM:** +X.X%
- **Capacity Utilization:** XX.X% | **Benchmark:** 78–82%
- **Interpretation:** [1-2 sentences on whether industry is running hot or has slack]

---

### Durable Goods Confirmation — Sector Earnings

#### Transportation
| Company | Rev (Recent Q) | YoY | Key Volume Metric | vs. Prior | Demand Signal |
|---|---|---|---|---|---|
| Boeing (BA) | $X.XB | +/-X% | XX deliveries | +/-X% | [Confirming / Conflicting / Neutral] |
| Union Pacific (UNP) | $X.XB | +/-X% | XXXk carloadings | +/-X% | [Confirming / Conflicting / Neutral] |
| FedEx (FDX) | $X.XB | +/-X% | X.XM avg daily pkg | +/-X% | [Confirming / Conflicting / Neutral] |

**Transportation read:** [1-2 sentences: are goods moving or stalling? Does this confirm or conflict with the durable goods print?]

#### Defense
| Company | Rev (Recent Q) | YoY | Backlog | YoY | Signal |
|---|---|---|---|---|---|
| Lockheed Martin (LMT) | $X.XB | +/-X% | $XXB | +/-X% | [Confirming / Neutral] |
| Raytheon (RTX) | $X.XB | +/-X% | $XXB | +/-X% | [Confirming / Neutral] |
| Northrop Grumman (NOC) | $X.XB | +/-X% | $XXB | +/-X% | [Confirming / Neutral] |

**Defense read:** [1 sentence: is defense spending driving durable goods, or is the private sector leading?]

---

### Industrial Production Confirmation — Sector Earnings

#### Raw Materials
| Company | Rev (Recent Q) | YoY | Key Volume Metric | vs. Prior | Signal |
|---|---|---|---|---|---|
| ArcelorMittal (MT) | $X.XB | +/-X% | X.XMt steel shipped | +/-X% | [Confirming / Conflicting / Neutral] |
| Alcoa (AA) | $X.XB | +/-X% | XXXkt aluminum shipped | +/-X% | [Confirming / Conflicting / Neutral] |
| Dow Inc (DOW) | $X.XB | +/-X% | Volume +/-X% YoY | — | [Confirming / Conflicting / Neutral] |

**Raw materials read:** [1-2 sentences: are industrial inputs being consumed at rates consistent with IP data?]

#### Consumer Goods
| Company | Rev (Recent Q) | YoY | Organic Vol Growth | Pricing | Signal |
|---|---|---|---|---|---|
| Procter & Gamble (PG) | $X.XB | +/-X% | +/-X% | +/-X% | [Confirming / Conflicting / Neutral] |
| Unilever (UL) | $X.XB | +/-X% | +/-X% | +/-X% | [Confirming / Conflicting / Neutral] |
| Coca-Cola (KO) | $X.XB | +/-X% | +/-X% cases | +/-X% | [Confirming / Conflicting / Neutral] |

**Consumer goods read:** [1-2 sentences: is end-demand healthy? Are companies growing through volume (real demand) or price alone (inflation-driven, demand stagnant)?]

---

### Divergences and Cross-Checks

[Flag any readings that conflict with each other — e.g., strong ISM Services PMI but weak consumer sentiment; strong NFP but declining durable goods core orders; strong IP data but raw material companies reporting volume declines. Divergences are the most actionable signals.]

- **ISM vs. Earnings:** [Do the PMI readings align with what transportation and manufacturing companies are reporting? Divergence = one of them is stale or distorted]
- **NFP vs. Consumer Sentiment:** [Are households confident despite strong hiring, or is confidence weak despite labor market strength? If confidence is declining despite strong NFP, watch for consumer spending deceleration with a 2-3 quarter lag]
- **Durable Goods vs. Transportation Volumes:** [Core orders tell you what was ordered; carloadings and FedEx volumes tell you what actually moved. Divergence between orders and shipments = either backlog building or demand cancellations]
- **Industrial Production vs. Raw Materials:** [If IP is strong but MT/AA volumes are declining, either industrial activity is less material-intensive (mix shift) or the IP data is lagged]
- **Building Permits vs. Rate Environment:** [Note current mortgage rate level — if permits are falling despite low rates, demand destruction is real; if permits are holding despite high rates, supply constraints dominate]

---

### Macro Implication for Portfolio

[2-3 sentences: what does this growth picture imply for sector positioning, asset allocation, and Fed policy? Specifically:]
- **Growth regime implication:** [Expansion = risk-on, cyclicals over defensives; Slowing = rotate toward quality; Contraction = defensives, credit caution]
- **Fed policy implication:** [Strong growth + strong employment = fewer/later cuts; Slowing growth + weak employment = cuts likely; Stagflation (slowing growth + sticky inflation) = Fed trapped]
- **Sector tilts implied:** [Which sectors look attractive or unattractive given this specific combination of indicators?]

---

### Save report
Save the full formatted report to:
`reports/growth-{YYYY-MM-DD}.md`
Report the file path when done.
