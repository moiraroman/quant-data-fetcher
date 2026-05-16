"""
Historical Price Fetcher — 30-Day OHLCV with JSON Cache
=========================================================
Fetch 30-day daily OHLCV bars from Yahoo Finance v8 Chart API.
Cache is stored per-ticker as cache/historical_{ticker}.json.
Historical bars never change → only re-fetch if today's bar is missing.

Usage:
    from fetchers.historical_prices import get_historical_prices
    bars = get_historical_prices(yahoo_fetcher, "SPY", days=30)
    # returns [{date, open, high, low, close, volume}, ...]
"""

import json
import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Cache directory: quant_data_fetcher/cache/
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(ticker: str) -> str:
    return os.path.join(CACHE_DIR, f"historical_{ticker}.json")


def _load_cache(ticker: str):
    """Returns cached bars list or None if absent/corrupt."""
    path = _cache_path(ticker)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, KeyError, OSError):
        pass
    return None


def _save_cache(ticker: str, bars: list):
    path = _cache_path(ticker)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(bars, f, ensure_ascii=False)
    except OSError as exc:
        logger.warning("Failed to write cache for %s: %s", ticker, exc)


def _parse_chart(raw: dict, days: int) -> list:
    """Parse Yahoo v8 chart response into list of daily bars."""
    chart_results = raw.get("chart", {}).get("result", [])
    if not chart_results:
        return []

    result = chart_results[0]
    timestamps = result.get("timestamp", [])
    indicators = result.get("indicators", {})
    quote = indicators.get("quote", [{}])[0] if indicators.get("quote") else {}

    opens = quote.get("open", [])
    highs = quote.get("high", [])
    lows = quote.get("low", [])
    closes = quote.get("close", [])
    volumes = quote.get("volume", [])

    bars = []
    for i, ts in enumerate(timestamps):
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        date_str = dt.strftime("%Y-%m-%d")
        o = _safe_get(opens, i)
        h = _safe_get(highs, i)
        l = _safe_get(lows, i)
        c = _safe_get(closes, i)
        v = _safe_get(volumes, i)

        # Skip bars with no data
        if h is None and l is None and c is None:
            continue

        bars.append({
            "date": date_str,
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": v,
        })

    # Return only the last N days
    return bars[-days:] if len(bars) > days else bars


def _safe_get(lst: list, idx: int):
    """Get list element safely, return None if out of bounds or None."""
    if idx < 0 or idx >= len(lst):
        return None
    val = lst[idx]
    return None if val is None else float(val)


def get_historical_prices(yahoo_fetcher, ticker: str, days: int = 30) -> list:
    """
    Returns 30-day OHLCV bars with JSON cache.

    Cache logic:
    - If cached bars exist and the last bar is today's date → return cache
    - Otherwise, fetch from Yahoo, save cache, return fresh data
    """
    _ensure_cache_dir()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    cached = _load_cache(ticker)

    # If cache is fresh (last bar = today), return it
    if cached and len(cached) > 0:
        last_date = cached[-1].get("date", "")
        if last_date == today_str:
            logger.debug("Historical cache HIT for %s (%d bars)", ticker, len(cached))
            return cached

    # Fetch from Yahoo v8 Chart API
    logger.info("Historical fetch for %s (cache=%s)", ticker, "miss" if cached else "empty")
    try:
        raw = yahoo_fetcher.get_chart(ticker, interval="1d", range_="1mo")
    except Exception as exc:
        logger.warning("Chart fetch failed for %s: %s", ticker, exc)
        return cached if cached else []

    bars = _parse_chart(raw, days)

    if bars:
        _save_cache(ticker, bars)
        logger.info("Cached %d bars for %s", len(bars), ticker)
    else:
        logger.warning("Empty bars parsed for %s", ticker)
        # Return stale cache if we have one
        if cached:
            return cached

    return bars
