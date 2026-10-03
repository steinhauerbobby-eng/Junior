---
name: dd
description: Full fundamental deep dive on a ticker. Runs the Fundamental Researcher agent for comprehensive valuation, earnings quality, competitive positioning, cash flow, and balance sheet analysis. Usage: /dd [TICKER] or /dd [TICKER] brief
when_to_use: Use when building a position or evaluating a name after the /light pass. Add "brief" for a fast 5-bullet summary instead of the full report.
---

The user will provide a ticker symbol. Run the **Fundamental Researcher** agent using yfinance, SEC/EDGAR filings, and Finviz data.

**If the argument includes "brief":** produce only the Brief Output below — skip the full report.
**Otherwise:** produce the Full Report.

---

## BRIEF OUTPUT (brief flag only)

**{TICKER} — DD Brief — {Date}**
- **Business:** [One sentence on what the company does and its primary revenue driver]
- **Financials:** Revenue $XB (+X% YoY) | Gross margin X% | Net income $Xm | FCF $Xm
- **Valuation:** $XX/share | P/E Xx | EV/EBITDA Xx | [Premium/Discount vs. peers — one phrase]
- **Biggest risk:** [Single most important risk in one sentence]
- **Verdict:** [Buy / Hold / Watch / Pass — one sentence with the key condition that would change the view]

---

## FULL REPORT

### 1. Business Model & Revenue Quality
- How does the company make money? Break down revenue streams.
- Is revenue recurring or transactional?
- Key unit economics: gross margin, take rate, ARPU, or equivalent
- Quality of earnings: are revenues durable and predictable?

### 2. Financial Summary (TTM / most recent full year)
Pull from yfinance and most recent 10-K/10-Q:
- Revenue (TTM), YoY growth rate
- Gross profit and gross margin
- EBITDA and EBITDA margin (GAAP and adjusted)
- Net income / net loss and net margin
- EPS (diluted, GAAP and adjusted)
- Free cash flow (operating cash flow minus capex)
- Cash and equivalents, total debt, net cash/debt position
- Shares outstanding and dilution trend (SBC as % of revenue)

### 3. Valuation
- Current price, market cap, enterprise value
- P/E (TTM and forward), EV/EBITDA, EV/Revenue, P/FCF, P/Book
- Compare to 5-8 closest peers on the same multiples
- Where does subject trade vs. peer median — premium or discount, and is it justified?
- Simple DCF sanity check: what growth and margin assumptions are implied by current price?

### 4. Earnings Quality & Key Risks
- GAAP vs. adjusted gap: what is management adding back and is it legitimate?
- Is FCF conversion strong relative to net income?
- What are the 3-5 biggest risks to the investment thesis?
- Any audit flags, going concern language, restatements, or unusual accounting in recent filings?

### 5. Competitive Positioning
- Who are the direct competitors and what is the market structure?
- Moat assessment: Wide / Narrow / None — and why?
- How defensible is the core competitive advantage?
- Customer concentration risk?

### 6. Recent Catalysts & News
- Most recent earnings: beat/miss vs. consensus, guidance, key management commentary
- Material 8-K events in the past 90 days
- Insider transactions (last 90 days): net buying or selling?
- Analyst sentiment: recent rating or price target changes if available

### 7. Investment Thesis

**Bull case (3 bullet points):**

**Bear case (3 bullet points):**

**Verdict:** [2-3 sentences: buy, hold, watch, or pass? Most important variable to monitor? What would change the view?]

---

Be specific with actual numbers. Do not fabricate data — if a metric is unavailable, say so.
