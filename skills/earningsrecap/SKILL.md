---
name: earningsrecap
description: Analyzes the most recent earnings release for a ticker. Summarizes management guidance, analyst Q&A highlights, revision drivers (beat/miss attribution, 10-K Item 7 MD&A context, EPS surprise history), acknowledged risks, and other notable commentary. Usage: /earningsrecap [TICKER] or /earningsrecap [TICKER] brief
when_to_use: Use immediately after a portfolio or watchlist company reports earnings, or when reviewing a company's most recent quarter before initiating a position. Add "brief" for a fast 3-bullet summary.
---

The user will provide a ticker symbol. Use the **Fundamental Researcher** agent with SEC/EDGAR (8-K earnings release, prior quarter 8-K for delta comparison, 10-K Item 7 MD&A, earnings call transcript if available) and Alpha Vantage news. Pull the most recent earnings event.

**If the argument includes "brief":** produce only the Brief Output below — skip the full report.
**Otherwise:** run two Python calls first (import with `sys.path.insert(0, 'src/data')`):
1. `quarterly_delta(ticker)` from `src/data/catalyst.py` → YoY delta table
2. `earnings_surprise_history(ticker)` from `src/data/catalyst.py` → EPS surprise history table

---

## BRIEF OUTPUT (brief flag only)

**{TICKER} — Earnings Brief — Q{X} {YEAR}**
- **Result:** EPS $X.XX vs. $X.XX est ([beat/miss] X%) | Rev $XB vs. $XB est ([beat/miss] X%) | Key YoY: rev [+/-X%], gross margin [+/-Xbps]
- **Guidance:** [Raised/Maintained/Lowered] — [one sentence on the most important guidance change]
- **Thesis impact:** [Strengthens / Weakens / Neutral — one sentence on why]

---

---

## EARNINGS RECAP — {TICKER} — Q{X} {YEAR}

**Report date:** [Date]
**EPS:** $X.XX actual vs. $X.XX estimate ([beat/miss] by X%)
**Revenue:** $X.XXB actual vs. $X.XXB estimate ([beat/miss] by X%)

---

### Management Guidance

**Full-year guidance:**
- Revenue: [range or figure] vs. prior guide of [X] and consensus of [X]
- EPS/EBITDA: [range or figure] vs. prior guide of [X] and consensus of [X]

**Q{next quarter} guidance:**
- [Key metrics guided]

**Tone:** [Raised / Maintained / Lowered / No guidance provided]
**Notable changes:** [Any changes to segment guidance, margin targets, capex plans]

---

### Analyst Q&A Highlights
[5-7 bullet points covering the most important exchanges — focus on questions that reveal analyst concerns or management conviction on key thesis drivers]

- **[Topic]:** [What was asked and what management said — 2 sentences max per point]

---

### Earnings Delta — vs. Same Quarter Prior Year (YoY)

*Quantitative table populated from `quarterly_delta(ticker)` (import `sys.path.insert(0, 'src/data')`). Qualitative bullets from WebFetch of prior year same-quarter 8-K via `sec_client.get_filings(ticker)`.*

**Quantitative (YoY — {prior_year_quarter} vs. {current_quarter})**
| Metric | Prior Year Q | This Q | YoY Change |
|---|---|---|---|
| Revenue | $XXXm | $XXXm | [+/-X%] |
| Gross Margin | XX.X% | XX.X% | [+/-X bps] |
| EBITDA | $XXm | $XXm | [+/-X%] |
| EBITDA Margin | XX.X% | XX.X% | [+/-X bps] |
| Net Income | $XXm | $XXm | [+/-X%] |
| EPS | $X.XX | $X.XX | [+/-$X.XX] |

*Note: if fewer than 5 quarters of history are available, comparison falls back to prior quarter (QoQ) and is labeled accordingly in the `comparison` field.*

**Qualitative (vs. same-quarter prior year 8-K)**
- **Guidance tone:** [More constructive / More cautious / Unchanged — cite specific language change if notable]
- **Strategic narrative:** [Any new emphasis or de-emphasis vs. same quarter last year: new segment/product highlighted, prior theme dropped, geographic shift]
- **Risk profile:** [New risks called out that weren't present a year ago, or prior risks now resolved/reduced]

---

### Revision Drivers

To populate this section, the agent must:
1. Call `earnings_surprise_history(ticker)` from `src/data/catalyst.py` (import with `sys.path.insert(0, 'src/data')`) for the EPS table
2. Read the 8-K earnings release for per-metric beat/miss attribution
3. Use `sec_client.get_filings(ticker)` to get the most recent 10-K URL, then WebFetch that filing to read **Item 7 — Management's Discussion and Analysis** — extract the annual narrative on revenue drivers, margin structure, and segment dynamics, then compare to this quarter's results

**EPS Surprise History (last 8 quarters)**
| Quarter | Date | EPS Est | EPS Actual | Surprise % | Beat/Miss |
|---|---|---|---|---|---|
| Q4 YYYY | YYYY-MM-DD | $X.XX | $X.XX | +X% | BEAT |
| ... | | | | | |

- **Surprise trend:** [Consistent beater / Improving / Declining / Volatile — from `surprise_trend` field]
- **Current streak:** [X consecutive beats / X consecutive misses]

**Beat/Miss Attribution — This Quarter (from 8-K)**

| Metric | Result vs. Consensus | Driver (Management-Cited) |
|---|---|---|
| Revenue | [Beat +X% / Miss -X% / In-line] | [Specific segment, product, or pricing factor mgmt cited] |
| Gross margin | [Beat +Xbp / Miss -Xbp] | [Cost or mix factor mgmt cited] |
| EBITDA | [Beat +X% / Miss -X%] | [Specific items driving the variance] |
| [Other key metric] | ... | ... |

**10-K Item 7 MD&A Context**
*What management described as the primary business drivers in the most recent annual filing — and whether this quarter aligned or diverged:*
- **Revenue drivers (per 10-K):** [Structural growth drivers management described in the annual report]
- **Margin trajectory (per 10-K):** [Transitory vs. structural headwinds/tailwinds management described annually]
- **Segment dynamics (per 10-K):** [Key segment commentary from the annual filing]
- **Quarter vs. 10-K narrative:** [Did this quarter's results align with the trajectory management laid out in the 10-K? Divergences — either positive or negative — are the most important revision signals to flag]

**Surprise Factors**
- **Primary beat drivers:** [Specific factors that exceeded analyst expectations — quote management where possible]
- **Primary miss drivers:** [Specific factors that disappointed — include if management explicitly acknowledged them]
- **Largest single delta from consensus:** [The one biggest surprise this quarter and what caused it]

**Sell-Side Focus Areas (Forward Revision Signals)**
[Which topics drew the most analyst questions in Q&A? These are where estimate revisions are most likely to flow:]
- **[Topic 1]:** [What management said and the implication for forward estimates]
- **[Topic 2]:** ...

**Forward Revision Outlook**
[2-3 sentences combining: 8-K guidance, 10-K MD&A baseline, and Q&A signals. Identify which specific line items face the highest upward or downward revision risk and whether the driver is structural (persistent) or one-time (fading). Flag magnitude where estimable.]

---

### Acknowledged Risks
[Risks management explicitly called out on the call or in the release]
- [Risk 1]
- [Risk 2]
- [Risk 3]

---

### Other Notable Commentary
[Any strategic announcements, M&A commentary, capital allocation updates, or off-script moments worth flagging]

---

### Thesis Impact
[2-3 sentences: does this earnings report strengthen, weaken, or maintain the investment thesis? What's the key takeaway for a current or prospective holder?]
