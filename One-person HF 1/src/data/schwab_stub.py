"""
Schwab API stub — placeholder until API approval is granted.
All methods return mock responses and log intended actions.
Replace with real Schwab API client when credentials are available.

Schwab API docs: https://developer.schwab.com
"""

import json
import logging
import os
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SCHWAB STUB] %(message)s")
logger = logging.getLogger(__name__)

SCHWAB_API_KEY = os.getenv("SCHWAB_API_KEY", "PENDING")
SCHWAB_SECRET = os.getenv("SCHWAB_SECRET", "PENDING")
API_READY = SCHWAB_API_KEY != "PENDING"


def _stub_warning(method: str):
    logger.warning(f"{method} called — Schwab API not yet connected. Manual execution required.")


def get_account_summary() -> dict:
    _stub_warning("get_account_summary")
    return {
        "status": "stub",
        "message": "Schwab API pending approval. Update SCHWAB_API_KEY and SCHWAB_SECRET in .claude/settings.json when approved.",
        "manual_action": "Log into Schwab web platform for current account summary.",
    }


def get_positions() -> dict:
    _stub_warning("get_positions")
    return {
        "status": "stub",
        "message": "Positions not yet synced from Schwab. Maintain positions manually in data/hedge_fund.db.",
        "manual_action": "Update positions table in SQLite via init_db.py or direct SQL.",
    }


def get_quotes(tickers: list[str]) -> dict:
    _stub_warning("get_quotes")
    return {
        "status": "stub",
        "message": "Use yfinance_client.py for real-time quotes until Schwab API is connected.",
        "tickers": tickers,
    }


def place_order(ticker: str, action: str, shares: float, order_type: str = "market", limit_price: float = None) -> dict:
    _stub_warning("place_order")
    order_details = {
        "ticker": ticker,
        "action": action,
        "shares": shares,
        "order_type": order_type,
        "limit_price": limit_price,
        "timestamp": datetime.now().isoformat(),
        "status": "MANUAL_REQUIRED",
    }
    logger.info(f"ORDER TICKET (manual execution required): {json.dumps(order_details)}")
    return {
        "status": "stub",
        "message": "Schwab API not yet connected. Execute this order manually.",
        "order_ticket": order_details,
        "manual_action": f"Log into Schwab and place {action.upper()} order: {shares} shares of {ticker} ({order_type}{'@'+str(limit_price) if limit_price else ''})",
    }


def get_order_history(days: int = 30) -> dict:
    _stub_warning("get_order_history")
    return {
        "status": "stub",
        "message": "Order history not yet synced from Schwab. Maintain trade_log in data/hedge_fund.db manually.",
    }


# MCP stdio interface
TOOLS = {
    "get_account_summary": lambda **_: get_account_summary(),
    "get_positions": lambda **_: get_positions(),
    "get_quotes": get_quotes,
    "place_order": place_order,
    "get_order_history": get_order_history,
}

if __name__ == "__main__":
    if not API_READY:
        logger.info("Running in STUB mode — Schwab API credentials not set.")

    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            tool = request.get("tool")
            params = request.get("params", {})
            if tool in TOOLS:
                result = TOOLS[tool](**params)
                print(json.dumps({"result": result}), flush=True)
            else:
                print(json.dumps({"error": f"Unknown tool: {tool}"}), flush=True)
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)
