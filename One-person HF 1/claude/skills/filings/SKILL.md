---
name: filings
description: Retrieves and organizes links to SEC filings (10-K, 10-Q, 8-K, DEF14A), investor relations page, investor decks, and other key company documents for a given ticker. Usage: /filings [TICKER]
when_to_use: Use when starting research on a new name or when you need quick access to official filings and IR materials.
---

The user will provide a ticker symbol. Use the SEC/EDGAR API to retrieve filing links. Also retrieve the company's investor relations URL.

EDGAR API endpoints to use:
- Company search: `https://efts.sec.gov/LATEST/search-index?q=%22{TICKER}%22&dateRange=custom&startdt={1_year_ago}&enddt={today}&forms=10-K,10-Q,8-K,DEF14A`
- Company facts: `https://data.sec.gov/submissions/CIK{CIK}.json`

Include the User-Agent header: `HedgeFund steinhauerbobby@gmail.com`

---

## FILINGS — {TICKER} ({COMPANY NAME})

### SEC Filings

**Annual Reports (10-K)**
- [FY Year] 10-K — [Direct EDGAR link] — Filed [Date]
- [FY Year-1] 10-K — [Direct EDGAR link] — Filed [Date]

**Quarterly Reports (10-Q)**
- Q[X] [Year] 10-Q — [Direct EDGAR link] — Filed [Date]
- Q[X-1] [Year] 10-Q — [Direct EDGAR link] — Filed [Date]
- Q[X-2] [Year] 10-Q — [Direct EDGAR link] — Filed [Date]

**Current Reports (8-K)** (last 90 days)
- [Date] 8-K — [Subject/topic] — [Direct EDGAR link]
- [Date] 8-K — [Subject/topic] — [Direct EDGAR link]

**Proxy Statement (DEF14A)**
- [Year] Proxy — [Direct EDGAR link] — Filed [Date]

---

### Investor Relations

**IR Homepage:** [URL]
**Earnings Releases:** [URL if separate page]
**Investor Decks / Presentations:** [URL or list of recent deck links]
**Earnings Call Transcripts:** [Link to transcript service or SEC filing if available]
**SEC EDGAR company page:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={CIK}&type=&dateb=&owner=include&count=40

---

### Notes
[Any filing irregularities, late filings, restatements, or unusual 8-K activity worth flagging]
