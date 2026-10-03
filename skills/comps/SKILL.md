---
name: comps
description: Builds a comparable company analysis table for a ticker and its peers. Tickers on rows, metrics on columns. Includes Median and Average rows. Outputs to Excel in reports/. Usage: /comps [TICKER] or /comps [TICKER] [PEER1] [PEER2] ...
when_to_use: Use when valuing a company relative to peers, building a position, or preparing a research summary. Specify peers manually to skip auto-selection and run faster.
---

The user will provide a subject ticker, and optionally a list of peer tickers.

## Peer selection
- **If peers are specified** (e.g., `/comps HIMS TDOC DOCS LFMD`): use exactly those tickers — do not add or substitute any.
- **If no peers specified** (e.g., `/comps HIMS`): use yfinance to identify 5-8 comparable peers with similar business models, revenue scale (0.3x–3x), and geography.

## Pull metrics for each company (subject + all peers)

Use yfinance for each ticker:
- Market cap ($B), enterprise value ($B)
- Revenue TTM ($B), revenue growth YoY %
- Gross margin %, EBITDA margin %, net income margin %
- P/E (TTM), P/E (Fwd), EV/EBITDA, EV/Sales, P/FCF, P/Book
- Net debt / EBITDA, ROE

For Median and Average rows: compute across all tickers (subject + peers) for each numeric metric. Skip NM/null values in both calculations.

## Output

**Tickers on rows, metrics on columns. Subject company row highlighted.**

## COMPS — {TICKER} vs. Peers — {Date}

| Ticker | Mkt Cap | EV | Rev ($B) | Rev Gth | Gross Mgn | EBITDA Mgn | P/E TTM | P/E Fwd | EV/EBITDA | EV/Sales | P/FCF | ND/EBITDA | ROE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **{TICKER}** | | | | | | | | | | | | | |
| Peer 1 | | | | | | | | | | | | | |
| Peer 2 | | | | | | | | | | | | | |
| ... | | | | | | | | | | | | | |
| **Median** | | | | | | | | | | | | | |
| **Average** | | | | | | | | | | | | | |

**{TICKER} vs. Median:** EV/EBITDA [X% premium/discount] | P/E Fwd [X% premium/discount] | EV/Sales [X% premium/discount]
**Assessment:** [1-2 sentences on whether subject trades at a justified premium/discount vs. peers and why]

---

Then save to Excel using openpyxl:
- File: `reports/comps-{TICKER}-{YYYY-MM-DD}.xlsx`
- Sheet 1: Comps table — tickers as rows, metrics as columns
  - Subject row: blue fill, white bold font
  - Median row: light green fill, bold
  - Average row: light yellow fill, bold
  - Column widths auto-fitted
- Sheet 2: Raw data with timestamps

Report the full file path when done.
