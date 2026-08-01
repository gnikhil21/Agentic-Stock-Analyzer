"""
Stock Monitoring Agent — Step 1: Data Tools
=============================================
These are the "tools" your LLM agent will later call. Keep them as plain,
well-tested Python functions first — no AI involved yet. Once these are
solid, you'll wire them into an LLM's function-calling loop (Step 2).

Install deps:
    pip install yfinance feedparser --break-system-packages

Run this file directly to sanity-check everything works:
    python stock_agent_tools.py
"""

import yfinance as yf
import feedparser
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from langchain_core.tools import tool


# ---------------------------------------------------------------------------
# TOOL 1: Current price + % change
# ---------------------------------------------------------------------------
@tool
def get_stock_price(ticker: str) -> dict:
    """
    Returns current price, day change %, and volume for a given ticker.

    Args:
        ticker: NSE ticker with .NS suffix (e.g. "HINDALCO.NS", "SUZLON.NS")

    Returns:
        dict with keys: ticker, price, change_pct, volume, currency
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")  # need 2 days to compute % change

        if hist.empty or len(hist) < 2:
            return {"ticker": ticker, "error": "No data available"}

        prev_close = hist["Close"].iloc[-2]
        latest_close = hist["Close"].iloc[-1]
        change_pct = ((latest_close - prev_close) / prev_close) * 100

        return {
            "ticker": ticker,
            "price": round(latest_close, 2),
            "change_pct": round(change_pct, 2),
            "volume": int(hist["Volume"].iloc[-1]),
            "currency": "INR",
        }
    except Exception as e:
        # Never let one bad ticker crash the whole watchlist run.
        # Your future agent needs to keep going even if one data source fails.
        return {"ticker": ticker, "error": str(e)}


# ---------------------------------------------------------------------------
# TOOL 2: Price history (for trend context, e.g. is this a breakout or noise?)
# ---------------------------------------------------------------------------
@tool
def get_price_history(ticker: str, days: int = 30) -> dict:
    """
    Returns OHLC price history for the last N days.

    Args:
        ticker: NSE ticker with .NS suffix
        days: number of calendar days to look back

    Returns:
        dict with ticker and a list of daily OHLC records
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=f"{days}d")

        if hist.empty:
            return {"ticker": ticker, "error": "No data available"}

        records = [
            {
                "date": str(idx.date()),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
            }
            for idx, row in hist.iterrows()
        ]

        return {"ticker": ticker, "history": records}
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


# ---------------------------------------------------------------------------
# TOOL 3: News search (free, no API key — Google News RSS)
# ---------------------------------------------------------------------------
@tool
def search_news(query: str, max_results: int = 5) -> list[dict]:
    """
    Fetches recent news headlines for a query using Google News RSS.
    Good enough for a v1 — swap for NewsAPI/a paid source later if you
    need better coverage or full article text.

    Args:
        query: search term, e.g. "Hindalco Industries" or "Suzlon Energy"
        max_results: max number of headlines to return

    Returns:
        list of dicts with: title, link, published, source
    """
    try:
        encoded_query = quote_plus(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"

        feed = feedparser.parse(rss_url)
        results = []

        for entry in feed.entries[:max_results]:
            results.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "source": entry.get("source", {}).get("title", "Unknown") if hasattr(entry, "source") else "Unknown",
            })

        return results
    except Exception as e:
        return [{"error": str(e)}]


# ---------------------------------------------------------------------------
# TOOL 4: Convenience — check your whole watchlist at once
# ---------------------------------------------------------------------------
@tool
def check_watchlist(tickers: list[str], move_threshold: float = 2.0) -> dict:
    """
    Checks price movement for a list of tickers and flags which ones
    moved enough to be worth investigating further (this mirrors the
    logic your future agent will run before deciding to fetch news).

    Args:
        tickers: list of NSE tickers, e.g. ["HINDALCO.NS", "SUZLON.NS"]
        move_threshold: % change that counts as "significant"

    Returns:
        dict with 'all_prices' (every ticker) and 'flagged' (significant movers)
    """
    all_prices = [get_stock_price(t) for t in tickers]
    flagged = [
        p for p in all_prices
        if "change_pct" in p and abs(p["change_pct"]) >= move_threshold
    ]
    return {"all_prices": all_prices, "flagged": flagged}


