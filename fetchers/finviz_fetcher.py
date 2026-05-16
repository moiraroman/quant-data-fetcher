"""
Finviz 数据抓取器
==================
从 Finviz 行情页抓取技术面指标 — RSI、ATR、均线偏离、多周期收益率等。

Finviz 是少数直接 SSR 渲染数字（非 JS 动态加载）的免费站点，
因此可以通过 HTML 解析稳定获取技术指标。
"""

import re
import time
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from config import FINVIZ_USER_AGENT, REQUEST_TIMEOUT, FINVIZ_RATE_LIMIT

logger = logging.getLogger(__name__)

# Finviz 快照表字段名 → 规范化 key 的映射
_FIELD_MAP = {
    "RSI (14)": "rsi_14",
    "ATR (14)": "atr_14",
    "SMA20": "sma20_pct",
    "SMA50": "sma50_pct",
    "SMA200": "sma200_pct",
    "Beta": "beta",
    "Perf Week": "perf_week",
    "Perf Month": "perf_month",
    "Perf Quarter": "perf_quarter",
    "Perf Half Y": "perf_half_year",
    "Perf YTD": "perf_ytd",
    "Perf Year": "perf_year",
    "52W High": "week52_high_raw",
    "52W Low": "week52_low_raw",
    "Rel Volume": "rel_volume",
    "Avg Volume": "avg_volume_raw",
    "Prev Close": "prev_close",
    "AUM": "aum_raw",
    "NAV/sh": "nav_raw",
    "Volatility": "volatility_raw",
    "Change": "change_raw",
    "Volume": "volume_raw",
    "Price": "price",
    "EPS (ttm)": "eps_ttm",
    "P/E": "pe_ratio",
    "Forward P/E": "forward_pe",
    "PEG": "peg",
    "Dividend": "dividend_raw",
    "Dividend %": "dividend_pct",
    "Payout": "payout_ratio",
    "Shares Outstanding": "shares_outstanding",
    "Insider Own": "insider_own",
    "Insider Trans": "insider_trans",
    "Inst Own": "inst_own",
    "Inst Trans": "inst_trans",
    "Short Float": "short_float",
    "Short Ratio": "short_ratio",


    # 其他可扩展...
}


class FinvizFetcher:
    """Finviz 数据抓取器。内置简单限速以避免 IP 封禁。"""

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": FINVIZ_USER_AGENT})
        self._last_request: float = 0.0

    def _rate_limit(self):
        """确保请求间隔 >= FINVIZ_RATE_LIMIT 秒。"""
        elapsed = time.time() - self._last_request
        if elapsed < FINVIZ_RATE_LIMIT:
            time.sleep(FINVIZ_RATE_LIMIT - elapsed)
        self._last_request = time.time()

    def get_technicals(self, symbol: str) -> Optional[dict]:
        """
        抓取 Finviz 行情快照表中所有技术指标。

        返回 dict，key 为规范化名称（rsi_14, atr_14, sma20_pct ...），
        数值已做清洗（去 %、去单位后缀）。
        """
        url = f"https://finviz.com/quote.ashx?t={symbol}"
        self._rate_limit()

        resp = self._session.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            logger.warning("Finviz HTTP %d for %s", resp.status_code, symbol)
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", class_="snapshot-table2")
        if table is None:
            logger.warning("Finviz snapshot table not found for %s", symbol)
            return None

        # 解析: 每行包含不定数量的 <td>，按 key-value 成对排列
        raw = {}
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            for i in range(0, len(cells) - 1, 2):
                key = cells[i].get_text(strip=True)
                val = cells[i + 1].get_text(strip=True)
                raw[key] = val

        # 规范化
        result = {"_raw": raw}
        for finviz_key, norm_key in _FIELD_MAP.items():
            if finviz_key in raw:
                result[norm_key] = _clean_value(raw[finviz_key])

        return result


def _clean_value(raw_val: str):
    """
    清洗 Finviz 原始值。

    示例:
        "71.13"              → 71.13
        "2.67%"              → 2.67
        "724.87 -0.19%"      → {"value": 724.87, "from_high": -0.19}
        "79.54M"             → 79540000.0
        "737.93B"            → 737930000000.0
    """
    # 复合值 "A B%"
    m = re.match(r"^([\d.,]+)\s+([+-]?[\d.,]+)%$", raw_val)
    if m:
        return {"value": _to_float(m.group(1)), "change_pct": _to_float(m.group(2))}

    # 含单位后缀
    suffix_map = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}
    for suffix, mul in suffix_map.items():
        if raw_val.endswith(suffix):
            num = raw_val[:-1].replace(",", "")
            try:
                return float(num) * mul
            except ValueError:
                return raw_val

    # 纯百分比
    if raw_val.endswith("%"):
        return _to_float(raw_val[:-1])

    # 纯数字
    return _to_float(raw_val)


def _to_float(s: str) -> float:
    """安全字符串 → float。"""
    try:
        return float(s.replace(",", ""))
    except (ValueError, AttributeError):
        return 0.0
