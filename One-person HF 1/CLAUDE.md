# One-Person Hedge Fund — Operating Context

## Fund Style
Fundamental + macro, top-down research flow. Macro thesis informs sector and asset class tilts; fundamental analysis picks names within those themes. Live fund with active research and backtesting.

## Broker
Charles Schwab. API approval pending — all execution is currently manual. Do not attempt automated order submission.

## Primary Data Source
yfinance (prices, fundamentals, options chains, macro tickers). Supplemented by SEC/EDGAR, NewsAPI, Alpha Vantage, and Finviz.

## Research Flow
1. Macro Researcher establishes macro regime (rates, inflation, FX, PMI)
2. Macro context informs sector/asset class tilts
3. Fundamental Researcher analyzes individual names within those themes
4. Thesis Tracker monitors existing positions against original thesis
5. Catalyst Monitor flags news and events touching the book

## Risk Rules
- No single position >10% of portfolio at cost
- Max drawdown threshold: review required at -15% from HWM
- Concentration: no more than 40% in a single sector
- Position sizing inputs: conviction level, volatility (HV/IV), portfolio context
- All sizing decisions routed through Portfolio & Risk Manager

## Agents — When to Use Each

| Agent | Invoke when |
|---|---|
| **Chief of Staff** | Open-ended questions with no obvious single agent ("what should I look at today?", "is X worth sizing up?") |
| **Macro Researcher** | Need macro regime update, rate/yield/FX/inflation analysis |
| **Fundamental Researcher** | Deep analysis on a specific name — valuation, earnings, competitive position |
| **Thesis Tracker** | Checking whether an existing position thesis still holds |
| **Portfolio & Risk Manager** | Position sizing, drawdown check, exposure summary, P&L |
| **Catalyst Monitor** | What's happening in the news on portfolio names or watchlist |

Skills handle mechanical, predefined workflows — invoke agents for open-ended reasoning.

## Skills — Quick Reference

| Skill | Usage |
|---|---|
| `/morningbrief` | Daily macro synopsis, headlines, indicator results, bull/bear cases |
| `/growth` | US growth regime assessment — ISM PMIs, UMich, Building Permits, NFP, Durable Goods, Industrial Production vs. growth thresholds, confirmed by sector earnings (transportation, defense, raw materials, consumer goods) |
| `/liquidity` | Global liquidity assessment — Net Fed Liquidity (Fed BS − TGA − RRP), QT/QE pace, bank reserves, M2, credit growth, DXY, ECB/BOJ/PBOC balance sheets, cross-border flows. Outputs liquidity score (-10 to +10) and explicit risk asset tailwinds/headwinds |
| `/light [ticker]` | Porter's Five Forces + setup analysis (short interest, P/C OI, ownership, insiders) |
| `/earningsrecap [ticker]` | Earnings summary — guidance, analyst Q&A, risks, commentary |
| `/filings [ticker]` | Links to 10-K/Q, investor decks, IR page |
| `/comps [ticker]` | Comparable company table — valuation multiples + KPIs vs peers (outputs to Excel) |
| `/vol [ticker]` | HV vs IV, IV rank/percentile, vol regime |

## Positions & Watchlist
Stored in `data/hedge_fund.db` (SQLite). Current positions table includes: ticker, entry date, entry price, thesis summary, position size, stop level.

## File Conventions
- Research notes: `research/[ticker]-[date].md`
- Strategy definitions: `strategies/[name].py`
- Generated reports: `reports/[type]-[date].xlsx` (OneDrive synced)
- Backtests: `src/backtesting/`
