---
name: industry
description: Industry orientation report. Maps verticals, valuation methodologies, KPIs, value chain, top/worst performers (live data), macro sensitivity, and screening criteria for a given industry. Usage: /industry [industry name]
when_to_use: Use when entering a new industry or sector for the first time. Bridges top-down macro thesis to bottom-up company research — run before /light or /dd on specific names.
---

The user will provide a freeform industry or sector name (e.g., "vertical SaaS", "specialty pharma", "fintech lending", "residential solar"). Run the **Fundamental Researcher** and **Macro Researcher** agents in parallel, then synthesize their outputs into the report below. Save the final output to `reports/industry-[kebab-case-name]-[YYYY-MM-DD].md` using the Write tool.

---

## INDUSTRY REPORT — {INDUSTRY NAME} — {Date}

### 1. Industry Overview
[1 paragraph: what this industry does, the core economic activity, why it exists, rough total addressable market size, and the primary growth driver(s)]

---

### 2. Verticals & Lay of the Land

| Vertical | Description | Example Companies | Relative Attractiveness |
|---|---|---|---|
| [Vertical 1] | [1 sentence] | [2-3 names] | [High / Medium / Low] |
| [Vertical 2] | ... | ... | ... |
| [4-8 verticals total] | | | |

[1-2 sentence narrative on which vertical(s) are currently capturing the most growth or value, and why]

---

### 3. Value Chain

[Map who sits at each step of the value chain from upstream inputs to end customer. For each step: who the players are, what margin profile they tend to carry, and where moats historically form. Flag the step with the best historical risk/reward for equity investors.]

---

### 4. Industry Lifecycle Stage

**Stage:** [Embryonic / Growth / Mature / Declining]

[One sentence on what this stage implies for valuation multiples, growth expectations, and how aggressively to position]

---

### 5. Primary Valuation Methodologies

| Multiple | When Used | Typical Range | Why It Works Here |
|---|---|---|---|
| [e.g. EV/EBITDA] | [mature, profitable names] | [X-Xx] | [reason] |
| [e.g. EV/Revenue] | [pre-profit, high-growth] | [X-Xx] | [reason] |
| [3-5 multiples total] | | | |

[1-2 sentences on which methodology is most reliable in the current environment and why]

---

### 6. Key KPIs

| KPI | What It Measures | Good Reading | Bad Reading | Where to Find It |
|---|---|---|---|---|
| [KPI 1] | [description] | [threshold] | [threshold] | [10-K / earnings / industry data] |
| [KPI 2] | ... | ... | ... | ... |
| [6-10 KPIs total] | | | | |

---

### 7. Capital Intensity & Funding Model

[One paragraph: asset-heavy vs. asset-light, typical net debt/EBITDA range, how companies fund growth (FCF reinvestment, debt, equity raises), capex as % of revenue norms, and what this implies for FCF generation and balance sheet risk]

---

### 8. Competitive Dynamics

[Fragmented or consolidated? What is the typical HHI or CR4 (top-4 market share concentration)? What are the primary sources of competitive advantage at the industry level — scale, switching costs, network effects, IP, regulatory moat? What is the pricing environment — rational or commoditized? How quickly do competitive advantages erode?]

---

### 9. Regulatory Environment

- **Primary regulatory bodies:** [list]
- **Key existing rules:** [2-3 most important regulations and their practical effect]
- **Pending legislation / policy changes:** [anything in flight that could be a catalyst — positive or negative]
- **Regulatory tail risk:** [worst-case regulatory scenario and its likelihood]

---

### 10. Macro Sensitivities

| Macro Variable | Direction of Impact | Why |
|---|---|---|
| Interest rates ↑ | [Positive / Negative / Neutral] | [reason] |
| Inflation ↑ | [Positive / Negative / Neutral] | [reason] |
| USD strengthens | [Positive / Negative / Neutral] | [reason] |
| PMI / GDP growth ↑ | [Positive / Negative / Neutral] | [reason] |
| Credit spreads widen | [Positive / Negative / Neutral] | [reason] |
| [Industry-specific variable] | ... | ... |

**Most important macro drivers (top 2-3):** [call out the variables that matter most and why]

---

### 11. Top & Worst Performers

*Pull live data via yfinance for all entries below.*

**Top 5 by Market Cap**

| Ticker | Price | Mkt Cap | YTD Return | 1Y Return | Rev Growth YoY | Primary Multiple |
|---|---|---|---|---|---|---|
| [TICKER] | $XX | $XB | +X% | +X% | +X% | Xx |
| ... | | | | | | |

**Bottom 3 by 1-Year Price Performance**

| Ticker | 1Y Return | What Drove Underperformance |
|---|---|---|
| [TICKER] | -X% | [2-3 sentences on what went wrong] |
| ... | | |

---

### 12. M&A & Consolidation Trends

- **Historical deal frequency:** [active / moderate / rare — and trend direction]
- **Typical deal multiples:** [EV/EBITDA or EV/Revenue range paid in acquisitions]
- **Acquirer profile:** [who buys — strategic consolidators, PE, cross-industry giants?]
- **Target profile:** [who gets bought — subscale players, technology assets, distressed?]
- **Notable recent deals (last 2 years):** [2-4 specific transactions with deal size and multiple if available]
- **Consolidation trajectory:** [accelerating / stable / decelerating — and why]

---

### 13. Current Macro Regime Fit

*From Macro Researcher — based on today's rates, inflation, growth, and credit conditions.*

**Verdict:** [Favored / Neutral / Disfavored]

[1 paragraph connecting the current macro environment (specific yield levels, inflation trend, credit spread direction, PMI) to this industry's macro sensitivities from Section 10. Be explicit: "With the 10Y at X% and the 2s10s spread at +Xbps, this industry is [favored/disfavored] because..."]

---

### 14. Screening Criteria

*Use these filters to narrow the universe to names worth a `/light` pass.*

| Metric | Threshold | Why It Matters for This Industry |
|---|---|---|
| [Metric 1] | [> or < X] | [reason] |
| [Metric 2] | [> or < X] | [reason] |
| [6-8 metrics total] | | |

---

### 15. Suggested Names to Research

[3-5 specific tickers that pass the screening criteria above and fit the current macro regime. One sentence rationale each. Tag with the suggested next step.]

- **[TICKER]** — [rationale]. → `/light [TICKER]`
- **[TICKER]** — [rationale]. → `/dd [TICKER]`
- ...

---

*Report saved to: `reports/industry-[kebab-case-name]-[YYYY-MM-DD].md`*
