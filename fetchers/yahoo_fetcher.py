"""
Yahoo Finance 数据抓取器
==========================
通过 Yahoo Finance v7 Quote API + v8 Chart API 获取实时价格、基本面与历史数据。

流程: 获取 Cookie → 获取 Crumb → 查询数据
"""

import time
import logging
from typing import Optional

import requests

from config import YAHOO_USER_AGENT, YAHOO_CRUMB_TTL, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


class YahooFetcher:
    """Yahoo Finance 数据抓取器。自动管理 Cookie / Crumb 生命周期。"""

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": YAHOO_USER_AGENT})
        self._crumb: Optional[str] = None
        self._crumb_at: float = 0.0

    # ---- Crumb 管理 -------------------------------------------------------

    def _fetch_crumb(self) -> str:
        """获取新的 crumb（需要有效的 Cookie）。"""
        # 从 fc.yahoo.com 获取初始 Cookie
        self._session.get("https://fc.yahoo.com/", timeout=REQUEST_TIMEOUT)
        # 用 Cookie 换 crumb
        resp = self._session.get(
            "https://query2.finance.yahoo.com/v1/test/getcrumb",
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        crumb = resp.text.strip()
        if not crumb:
            raise RuntimeError("Yahoo Finance returned empty crumb")
        logger.debug("Got new Yahoo crumb: %s...", crumb[:8])
        return crumb

    def _ensure_crumb(self) -> str:
        """返回有效 crumb，过期自动刷新。"""
        now = time.time()
        if self._crumb is None or (now - self._crumb_at) > YAHOO_CRUMB_TTL:
            self._crumb = self._fetch_crumb()
            self._crumb_at = now
        return self._crumb

    # ---- 行情查询 ---------------------------------------------------------

    def get_quotes(self, symbols: list[str]) -> list[dict]:
        """
        获取指定符号的实时行情。

        返回 yahoo v7 quoteResponse.result 中的列表，
        每项包含: symbol, regularMarketPrice, regularMarketChange,
        regularMarketChangePercent, regularMarketDayHigh/Low,
        regularMarketPreviousClose, fiftyTwoWeekHigh/Low,
        regularMarketVolume, averageDailyVolume3Month,
        fiftyDayAverage, twoHundredDayAverage, marketCap,
        navPrice, totalAssets, beta, shortName, longName 等。
        """
        crumb = self._ensure_crumb()
        joined = ",".join(symbols)
        url = (
            f"https://query2.finance.yahoo.com/v7/finance/quote"
            f"?symbols={joined}&crumb={crumb}"
        )
        resp = self._session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        body = resp.json()
        result = body.get("quoteResponse", {}).get("result", [])
        if not result:
            logger.warning("Yahoo quote empty for %s (maybe invalid symbols)", symbols)
        return result

    def get_quote_single(self, symbol: str) -> Optional[dict]:
        """获取单个符号的行情。"""
        results = self.get_quotes([symbol])
        return results[0] if results else None

    # ---- 历史 K 线 --------------------------------------------------------

    def get_chart(
        self,
        symbol: str,
        interval: str = "1d",
        range_: str = "1mo",
    ) -> dict:
        """
        获取历史 OHLCV 数据。

        返回 v8 chart 结果，含 timestamps + indicators.quote[0].open/high/low/close/volume。
        """
        crumb = self._ensure_crumb()
        url = (
            f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"
            f"?interval={interval}&range={range_}&crumb={crumb}"
        )
        resp = self._session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    # ---- 便捷复合查询 -----------------------------------------------------

    def fetch_ticker_data(self, symbol: str) -> dict:
        """
        获取单标的的完整快照 (行情 + 日内范围 + 52周 + 均线 + K线)。
        """
        quote = self.get_quote_single(symbol)
        if quote is None:
            return {"symbol": symbol, "error": "no_quote_data"}

        chart_raw = {}
        try:
            chart_raw = self.get_chart(symbol, interval="1d", range_="3mo")
        except Exception as exc:
            logger.warning("Chart fetch failed for %s: %s", symbol, exc)

        return {
            "symbol": symbol,
            "name": quote.get("shortName") or quote.get("longName", ""),
            "price": quote.get("regularMarketPrice"),
            "change": quote.get("regularMarketChange"),
            "change_pct": quote.get("regularMarketChangePercent"),
            "day_high": quote.get("regularMarketDayHigh"),
            "day_low": quote.get("regularMarketDayLow"),
            "prev_close": quote.get("regularMarketPreviousClose"),
            "week52_high": quote.get("fiftyTwoWeekHigh"),
            "week52_low": quote.get("fiftyTwoWeekLow"),
            "volume": quote.get("regularMarketVolume"),
            "avg_volume": quote.get("averageDailyVolume3Month"),
            "ma_50": quote.get("fiftyDayAverage"),
            "ma_200": quote.get("twoHundredDayAverage"),
            "beta": quote.get("beta"),
            "market_cap": quote.get("marketCap"),
            "nav_price": quote.get("navPrice"),
            "total_assets": quote.get("totalAssets"),
            "market_state": quote.get("marketState", "UNKNOWN"),
            "chart_raw": chart_raw,
            "quote_raw": quote,
        }
