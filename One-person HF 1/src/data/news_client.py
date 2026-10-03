"""
News aggregator: NewsAPI + Alpha Vantage + Finviz.
Deduplicates headlines and attaches sentiment scores where available.
"""

import os
import sys
import time
from datetime import datetime, timedelta
from typing import Optional

import requests
from bs4 import BeautifulSoup

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "")


def _newsapi_fetch(query: str, days_back: int = 3) -> list[dict]:
    if not NEWSAPI_KEY:
        return []
    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "from": from_date,
        "sortBy": "relevancy",
        "language": "en",
        "pageSize": 10,
        "apiKey": NEWSAPI_KEY,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        return [
            {
                "source": "NewsAPI",
                "headline": a["title"],
                "summary": a.get("description", ""),
                "url": a["url"],
                "published": a["publishedAt"][:10],
                "sentiment": None,
            }
            for a in articles
        ]
    except Exception:
        return []


def _alpha_vantage_fetch(ticker: str) -> list[dict]:
    if not ALPHA_VANTAGE_KEY:
        return []
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker.upper(),
        "limit": 10,
        "apikey": ALPHA_VANTAGE_KEY,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        feed = resp.json().get("feed", [])
        results = []
        for item in feed:
            ticker_sentiment = next(
                (ts for ts in item.get("ticker_sentiment", []) if ts["ticker"] == ticker.upper()),
                None,
            )
            sentiment_label = ticker_sentiment.get("ticker_sentiment_label") if ticker_sentiment else item.get("overall_sentiment_label")
            results.append({
                "source": "Alpha Vantage",
                "headline": item["title"],
                "summary": item.get("summary", ""),
                "url": item["url"],
                "published": item["time_published"][:8],
                "sentiment": sentiment_label,
            })
        return results
    except Exception:
        return []


def _finviz_fetch(ticker: str) -> list[dict]:
    url = f"https://finviz.com/quote.ashx?t={ticker.upper()}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        news_table = soup.find("table", id="news-table")
        if not news_table:
            return []
        results = []
        current_date = ""
        for row in news_table.find_all("tr")[:15]:
            cols = row.find_all("td")
            if len(cols) < 2:
                continue
            date_cell = cols[0].text.strip()
            if len(date_cell) > 8:
                current_date = date_cell.split(" ")[0]
            headline_cell = cols[1]
            link = headline_cell.find("a")
            if link:
                results.append({
                    "source": "Finviz",
                    "headline": link.text.strip(),
                    "summary": "",
                    "url": link.get("href", ""),
                    "published": current_date,
                    "sentiment": None,
                })
        return results
    except Exception:
        return []


def _deduplicate(articles: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for a in articles:
        key = a["headline"].lower()[:60]
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique


def get_news(ticker: str, days_back: int = 3) -> dict:
    company_query = ticker  # In production, resolve ticker to company name
    all_articles = (
        _alpha_vantage_fetch(ticker)
        + _newsapi_fetch(company_query, days_back)
        + _finviz_fetch(ticker)
    )
    deduplicated = _deduplicate(all_articles)

    # Sort: Alpha Vantage first (has sentiment), then by date
    deduplicated.sort(key=lambda x: (x["sentiment"] is None, x["published"]), reverse=False)

    return {
        "ticker": ticker,
        "article_count": len(deduplicated),
        "sources_used": list({a["source"] for a in deduplicated}),
        "articles": deduplicated,
    }


def get_macro_news(topics: list[str] = None, days_back: int = 2) -> dict:
    if topics is None:
        topics = ["Federal Reserve interest rates", "inflation CPI", "GDP growth economy"]
    all_articles = []
    for topic in topics:
        all_articles.extend(_newsapi_fetch(topic, days_back))
        time.sleep(0.5)

    deduplicated = _deduplicate(all_articles)
    return {
        "topics": topics,
        "article_count": len(deduplicated),
        "articles": deduplicated,
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["newsapi", "alphavantage", "finviz", "all"], default="all")
    args = parser.parse_args()

    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            tool = request.get("tool")
            params = request.get("params", {})
            if tool == "get_news":
                print(json.dumps(get_news(**params)), flush=True)
            elif tool == "get_macro_news":
                print(json.dumps(get_macro_news(**params)), flush=True)
            else:
                print(json.dumps({"error": f"Unknown tool: {tool}"}), flush=True)
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)
