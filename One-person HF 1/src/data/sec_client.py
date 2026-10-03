"""
SEC EDGAR API client. Retrieves filings and company data from EDGAR.
No API key required. User-Agent header required by SEC.
"""

import time
from typing import Optional

import requests

HEADERS = {"User-Agent": "HedgeFund steinhauerbobby@gmail.com"}
EDGAR_BASE = "https://data.sec.gov"
EFTS_BASE = "https://efts.sec.gov"


def _get(url: str) -> dict:
    time.sleep(0.11)  # SEC rate limit: max 10 requests/second
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_cik(ticker: str) -> Optional[str]:
    data = _get(f"{EDGAR_BASE}/submissions/CIK{ticker.upper().zfill(10)}.json")
    return data.get("cik")


def search_company(ticker: str) -> dict:
    url = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom&forms=10-K,10-Q,8-K,DEF14A"
    data = _get(url)
    hits = data.get("hits", {}).get("hits", [])
    return {
        "ticker": ticker,
        "results": [
            {
                "form": h["_source"].get("form_type"),
                "filed": h["_source"].get("file_date"),
                "description": h["_source"].get("display_names"),
                "url": f"https://www.sec.gov/Archives/edgar/data/{h['_source'].get('entity_id')}/{h['_source'].get('file_num', '')}",
            }
            for h in hits[:20]
        ],
    }


def get_filings(ticker: str, form_types: list[str] = None) -> dict:
    if form_types is None:
        form_types = ["10-K", "10-Q", "8-K", "DEF14A"]

    # Get CIK from company tickers mapping
    tickers_data = _get("https://www.sec.gov/files/company_tickers.json")
    cik = None
    company_name = None
    for _, v in tickers_data.items():
        if v.get("ticker", "").upper() == ticker.upper():
            cik = str(v["cik_str"]).zfill(10)
            company_name = v.get("title")
            break

    if not cik:
        return {"error": f"Could not find CIK for ticker {ticker}"}

    submissions = _get(f"{EDGAR_BASE}/submissions/CIK{cik}.json")
    filings = submissions.get("filings", {}).get("recent", {})

    forms = filings.get("form", [])
    dates = filings.get("filingDate", [])
    accessions = filings.get("accessionNumber", [])
    descriptions = filings.get("primaryDocument", [])

    result = {"ticker": ticker, "company": company_name, "cik": cik, "filings": {}}
    for form_type in form_types:
        result["filings"][form_type] = []

    for i, form in enumerate(forms):
        if form in form_types:
            accession_clean = accessions[i].replace("-", "")
            cik_int = str(int(cik))
            url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_clean}/{descriptions[i]}"
            result["filings"][form].append({
                "date": dates[i],
                "accession": accessions[i],
                "url": url,
                "edgar_viewer": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={form}&dateb=&owner=include&count=10",
            })
            if len(result["filings"][form]) >= 4:
                continue

    # Add IR page search
    result["ir_page"] = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=&dateb=&owner=include&count=40"
    return result


def get_recent_8k(ticker: str, days: int = 90) -> dict:
    from datetime import datetime, timedelta
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    filings = get_filings(ticker, form_types=["8-K"])
    recent = [f for f in filings.get("filings", {}).get("8-K", []) if f["date"] >= start]
    return {"ticker": ticker, "recent_8k": recent}
