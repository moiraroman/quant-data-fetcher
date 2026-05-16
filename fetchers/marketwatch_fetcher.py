"""
MarketWatch 行情抓取器
========================
从 MarketWatch 行情页提取价格与基础数据（作为 Yahoo 的双源验证）。

仅抓取文本渲染的价格数据（非 JS），适用于部分 ETF/ETN。
"""

import re
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from config import REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/132.0.0.0 Safari/537.36"
    ),
}


def get_marketwatch_quote(symbol: str) -> Optional[dict]:
    """
    获取 MarketWatch 行情快照。

    URL: https://www.marketwatch.com/investing/fund/{SYMBOL}
         https://www.marketwatch.com/investing/stock/{SYMBOL}

    返回: { "price", "change", "change_pct", "volume", "day_range", ... }
    """
    # 尝试 fund 和 stock 两种 URL
    for category in ("fund", "stock"):
        url = f"https://www.marketwatch.com/investing/{category}/{symbol.lower()}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            # Price: <bg-quote class="value">157.40</bg-quote>
            price_el = soup.find("bg-quote", class_="value")
            if not price_el:
                price_el = soup.find("span", class_="value")

            price = None
            if price_el:
                price_text = price_el.get_text(strip=True)
                price = _to_float(price_text)

            if price is None:
                continue

            # Change: <bg-quote class="change--percent--q" field="change">+3.10</bg-quote>
            change_el = soup.find("bg-quote", field="change")
            change_pct_el = soup.find("bg-quote", field="percentchange")

            change = _to_float(change_el.get_text(strip=True)) if change_el else None
            change_pct = _to_float(change_pct_el.get_text(strip=True)) if change_pct_el else None

            # 从页面文本提取更多字段（以表格行存在）
            extras = _parse_table(soup)

            return {
                "symbol": symbol.upper(),
                "price": price,
                "change": change,
                "change_pct": change_pct,
                "volume": _to_float(extras.get("Volume", "")),
                "day_range": extras.get("Day Range", ""),
                "week52_range": extras.get("52 Week Range", ""),
                "source": f"marketwatch.com/{category}",
                "url": url,
            }

        except requests.RequestException as exc:
            logger.debug("MW %s/%s: %s", symbol, category, exc)
            continue
        except Exception as exc:
            logger.debug("MW %s/%s parse: %s", symbol, category, exc)
            continue

    return None


def _parse_table(soup: BeautifulSoup) -> dict:
    """解析 MarketWatch 行情页的 Key-Value 表格。"""
    result = {}
    table = soup.find("table", class_="table--primary")
    if not table:
        return result
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) >= 2:
            key = cells[0].get_text(strip=True)
            val = cells[1].get_text(strip=True)
            result[key] = val
    return result


def _to_float(s: str) -> Optional[float]:
    """安全字符串 → float。"""
    if not s:
        return None
    s = s.replace(",", "").replace("$", "").replace("%", "").strip()
    try:
        return float(s)
    except (ValueError, TypeError):
        return None
