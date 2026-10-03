"""
Initialize the SQLite database schema.
Run once: python src/data/init_db.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parents[2] / "data" / "hedge_fund.db"


def init():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            entry_date TEXT NOT NULL,
            entry_price REAL NOT NULL,
            shares REAL NOT NULL,
            position_size_usd REAL NOT NULL,
            sector TEXT,
            thesis_summary TEXT,
            stop_level REAL,
            target_price REAL,
            conviction INTEGER CHECK(conviction BETWEEN 1 AND 5),
            status TEXT DEFAULT 'open' CHECK(status IN ('open', 'closed')),
            exit_date TEXT,
            exit_price REAL,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL UNIQUE,
            added_date TEXT NOT NULL,
            thesis_summary TEXT,
            target_entry REAL,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS iv_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            iv_30d_atm REAL,
            hv_20d REAL,
            hv_30d REAL,
            hv_60d REAL,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(ticker, date)
        );

        CREATE TABLE IF NOT EXISTS trade_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            action TEXT NOT NULL CHECK(action IN ('buy', 'sell', 'short', 'cover')),
            shares REAL NOT NULL,
            price REAL NOT NULL,
            total_usd REAL NOT NULL,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS research_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            date TEXT NOT NULL,
            category TEXT CHECK(category IN ('fundamental', 'macro', 'thesis', 'earnings', 'other')),
            title TEXT NOT NULL,
            content TEXT,
            file_path TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_positions_ticker ON positions(ticker);
        CREATE INDEX IF NOT EXISTS idx_iv_snapshots_ticker_date ON iv_snapshots(ticker, date);
        CREATE INDEX IF NOT EXISTS idx_trade_log_ticker ON trade_log(ticker);
        CREATE INDEX IF NOT EXISTS idx_watchlist_ticker ON watchlist(ticker);
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")


if __name__ == "__main__":
    init()
