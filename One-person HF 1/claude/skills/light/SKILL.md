---
name: light
description: Initial research pass on a ticker. Runs Porter's Five Forces competitive analysis plus a setup analysis covering short interest, put/call open interest, ownership profile, and recent insider transactions. Usage: /light [TICKER] or /light [TICKER] brief
when_to_use: Use when evaluating a new name before committing to a full fundamental deep dive. Add "brief" for a fast moat + setup signal summary.
---

The user will provide a ticker symbol. Run the **Fundamental Researcher** and **Setup Analyst** agents **in parallel**, then synthesize their outputs into the report below.

- **Fundamental Researcher** handles: Porter's Five Forces + overall moat assessment
- **Setup Analyst** handles: short interest, options market, ownership profile, insider transactions

**If the argument includes "brief":** produce only the Brief Output below.
**Otherwise:** produce the Full Report.

---

## BRIEF OUTPUT (brief flag only)

**{TICKER} — Light Brief — {Date}**
- **Moat:** [Wide / Narrow / None] — [one sentence reason]
- **Setup signals:** [3 most important signals from: short interest, UOA, institutional changes, insider activity]
- **Worth a full DD?** [Yes / No / Maybe — one sentence on what the key question is]

---

## FULL REPORT

## LIGHT PASS — {TICKER}

### Porter's Five Forces

**1. Threat of New Entrants** — [Low/Medium/High]
[2-3 sentences: capital requirements, regulatory barriers, brand moats, economies of scale]

**2. Bargaining Power of Suppliers** — [Low/Medium/High]
[2-3 sentences: supplier concentration, switching costs, input criticality]

**3. Bargaining Power of Buyers** — [Low/Medium/High]
[2-3 sentences: customer concentration, price sensitivity, switching costs]

**4. Threat of Substitutes** — [Low/Medium/High]
[2-3 sentences: alternative products, switching costs for end users]

**5. Competitive Rivalry** — [Low/Medium/High]
[2-3 sentences: number of competitors, market share concentration, pricing dynamics]

**Overall Moat Assessment:** [Wide / Narrow / None] — [one sentence]

---

### Setup Analysis

**Short Interest**
- Short % of float: XX%
- Days to cover: X.X
- Short interest trend: [increasing/decreasing]
- Interpretation: [squeeze risk? crowded short? muted?]

**Options Market**
- Put/Call Open Interest ratio: X.XX
- Implied move (nearest expiry): ±X%
- Notable positioning: [unusual OI concentration at specific strikes]

**Ownership Profile**
- Institutional ownership: XX%
- Top 5 institutional holders and recent changes (13F data)
- Insider ownership: XX%

**Recent Insider Transactions** (last 90 days)
- [Name, Title, Transaction type, Shares, Date]
- Interpretation: [net buying? selling? routine 10b5-1?]

---

### Verdict
[2-3 sentences: is this worth a full DD? What's the most important thing to investigate next?]

Use `/dd {TICKER}` for a full fundamental analysis.
