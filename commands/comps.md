---
name: comps
description: Builds a comparable company analysis table for a ticker and its peers. Pulls valuation multiples (P/E, EV/EBITDA, P/FCF, P/S, EV/Sales) and key KPIs from yfinance. Outputs to a local Excel workbook in the reports/ folder. Usage: /comps [TICKER]
when_to_use: Use when valuing a company relative to peers, building a position, or preparing a research summary.
---

The user will provide a ticker symbol. Use yfinance to identify the company's sector and pull peer tickers. Build a comps table.

## Step 1 — Identify peers
Use yfinance to get the company's sector and industry. Identify 5-8 comparable peers in the same industry. Prefer companies with similar business models, revenue scale (within 0.3x-3x), and geography.

## Step 2 — Pull metrics for each company (subject + all peers)

For each company pull from yfinance:
- Market cap
- Enterprise value
- Price
- 52-week high/low
- Revenue (TTM)
- Revenue growth (YoY %)
- Gross margin %
- EBITDA margin %
- Net income margin %
- EPS (TTM)
- P/E (TTM and forward)
- EV/EBITDA (TTM)
- EV/Sales (TTM)
- P/FCF
- P/Book
- Net debt / EBITDA
- Return on equity (ROE)
- Return on invested capital (ROIC)

## Step 3 — Output

Present as a formatted table in the conversation first:

---

## COMPS — {TICKER} vs. Peers

| Metric | {TICKER} | Peer 1 | Peer 2 | Peer 3 | Peer 4 | Peer 5 | Median |
|---|---|---|---|---|---|---|---|
| Market Cap ($B) | | | | | | | |
| EV ($B) | | | | | | | |
| Rev Growth YoY | | | | | | | |
| Gross Margin | | | | | | | |
| EBITDA Margin | | | | | | | |
| P/E (TTM) | | | | | | | |
| P/E (Fwd) | | | | | | | |
| EV/EBITDA | | | | | | | |
| EV/Sales | | | | | | | |
| P/FCF | | | | | | | |
| Net Debt/EBITDA | | | | | | | |
| ROE | | | | | | | |

**{TICKER} vs. Median:** [Premium/Discount] on EV/EBITDA: [X%] | P/E: [X%]
**Assessment:** [1-2 sentences on whether the subject trades at a justified premium/discount vs. peers and why]

---

Then call the `excel` MCP server using the `write_comps` tool to save the data locally:
- File saved to: `reports/comps-{TICKER}-{date}.xlsx`
- Sheet 1: Comps table (formatted, subject company highlighted in blue)
- Sheet 2: Raw data with timestamps

Report the full file path to the user when done so they can open it directly in Excel.
