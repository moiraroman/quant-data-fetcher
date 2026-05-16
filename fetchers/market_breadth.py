"""
Market Breadth Fetcher
======================
市场宽度数据（NH/NL, Advance/Decline）。
主源: Yahoo Finance 的 NYSE market breadth 数据。
"""

import logging
from datetime import datetime
from typing import Optional

import requests

logger = logging.getLogger("market_breadth_fetcher")

BREADTH_URL = "https://query1.finance.yahoo.com/v8/finance/chart/^NYA"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/132.0.0.0 Safari/537.36"
    ),
}
TIMEOUT = 15


def get_market_breadth() -> dict:
    """
    获取市场宽度数据。
    从 Yahoo 和公开源合并。

    返回:
    {
      nyse_advance_decline: { advances, declines, unchanged, total },
      nyse_nhnl: { new_highs, new_lows },
      signal: BULLISH / NEUTRAL / BEARISH,
      source
    }
    """
    result = {
        "fetched_at": datetime.now().isoformat(),
        "nyse_advance_decline": None,
        "nyse_nhnl": None,
        "signal": "NEUTRAL",
        "source": "yahoo+finviz",
    }

    # 尝试 Yahoo 市场数据
    try:
        resp = requests.get(BREADTH_URL, headers=HEADERS, timeout=TIMEOUT)
        data = resp.json()
        chart = data.get("chart", {}).get("result", [{}])[0]
        meta = chart.get("meta", {})
        result["nyse_index"] = {
            "symbol": "^NYA",
            "price": meta.get("regularMarketPrice"),
            "change": meta.get("regularMarketChange"),
            "change_pct": meta.get("regularMarketChangePercent"),
            "prev_close": meta.get("chartPreviousClose"),
        }
    except Exception as exc:
        logger.warning("Yahoo breadth error: %s", exc)
        result["nyse_index"] = {"error": str(exc)}

    # 从 FRED 尝试获取 Advance/Decline (fallback)
    try:
        import requests as r2
        fred_url = ("https://fred.stlouisfed.org/graph/fredgraph.csv"
                    "?id=NYSEADV&id=NYSEDEC&cosd=2020-01-01")
        resp2 = r2.get(fred_url, headers=HEADERS, timeout=TIMEOUT)
        if resp2.status_code == 200:
            lines = resp2.text.strip().split("\n")
            if len(lines) > 1:
                last = lines[-1].split(",")
                if len(last) >= 3:
                    adv = last[1]
                    dec = last[2]
                    result["nyse_advance_decline"] = {
                        "advances": adv.strip(),
                        "declines": dec.strip(),
                        "source": "FRED",
                    }
    except Exception:
        pass

    # 计算信号
    if result.get("nyse_advance_decline"):
        try:
            adv_val = float(result["nyse_advance_decline"]["advances"])
            dec_val = float(result["nyse_advance_decline"]["declines"])
            if adv_val + dec_val > 0:
                ratio = adv_val / (adv_val + dec_val)
                if ratio > 0.60:
                    result["signal"] = "BULLISH"
                elif ratio < 0.40:
                    result["signal"] = "BEARISH"
                else:
                    result["signal"] = "NEUTRAL"
                result["advance_ratio"] = round(ratio, 3)
        except (ValueError, TypeError):
            pass

    return result


def get_sector_performance() -> dict:
    """
    获取 GICS 11 大板块表现。
    使用 YahooFetcher 类 (已有 cookie/crumb 逻辑) 而非直接 API。
    """
    sector_etfs = {
        "XLK": "Technology", "XLF": "Financials", "XLV": "Health Care",
        "XLE": "Energy", "XLI": "Industrials",
        "XLP": "Consumer Staples", "XLY": "Consumer Discretionary",
        "XLU": "Utilities", "XLB": "Materials",
        "XLRE": "Real Estate", "XLC": "Communication Services",
    }

    symbols = list(sector_etfs.keys())

    try:
        from fetchers.yahoo_fetcher import YahooFetcher
        yf = YahooFetcher()
        quotes = yf.get_quotes(symbols)

        sectors = {}
        for q in quotes:
            sym = q.get("symbol")
            if sym in sector_etfs:
                sectors[sym] = {
                    "name": sector_etfs[sym],
                    "price": q.get("regularMarketPrice"),
                    "change_pct": q.get("regularMarketChangePercent"),
                }

        logger.info("Sector perf: %d sectors", len(sectors))
        return sectors

    except Exception as exc:
        logger.error("Sector perf error: %s", exc)
        return {}
