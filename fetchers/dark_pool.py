"""
Dark Pool / Off-Exchange Volume Fetcher v2
==========================================
从 ChartExchange 抓取暗池/场外交易量数据。
BS4 静态 HTML 抓取，数据直接嵌在 HTML table 中。
"""

import logging
import re
from datetime import datetime
from typing import Optional

import requests

logger = logging.getLogger("dark_pool_fetcher")

CHARTEXCHANGE_BASE = "https://chartexchange.com/symbol"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/132.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 15

EXCHANGE_MAP = {
    "SPY": "nyse-spy", "QQQ": "nasdaq-qqq", "IWM": "nyse-iwm",
    "DIA": "nyse-dia", "TLT": "nasdaq-tlt",
    "GDXU": "nyse-gdxu", "SOXX": "nasdaq-soxx",
    "HYG": "nyse-hyg", "JNK": "nyse-jnk",
}


def get_dark_pool_summary(ticker: str = "SPY") -> Optional[dict]:
    slug = EXCHANGE_MAP.get(ticker.upper(), f"nyse-{ticker.lower()}")
    url = f"{CHARTEXCHANGE_BASE}/{slug}/exchange-volume/"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception as exc:
        logger.error("ChartExchange [%s] HTTP error: %s", ticker, exc)
        return None

    text = resp.text

    result = {
        "ticker": ticker.upper(),
        "fetched_at": datetime.now().isoformat(),
        "source": "chartexchange.com",
    }

    # Parse summary: "Off Exchange & Dark Pool volume is 6,102,170, which is 32.94%"
    m = re.search(
        r"Off\s+Exchange\s+&?\s*Dark\s+Pool\s+volume\s+is\s+"
        r"([\d,]+(?:\.\d+)?)\s*,\s*which\s+is\s+([\d.]+)%",
        text, re.IGNORECASE
    )
    if m:
        result["off_exchange_volume"] = int(m.group(1).replace(",", ""))
        result["off_exchange_pct"] = float(m.group(2))

    # Parse lit volume from same paragraph
    m2 = re.search(
        r"Lit\s+volume\s+is\s+([\d,]+(?:\.\d+)?)\s*,\s*which\s+is\s+([\d.]+)%",
        text, re.IGNORECASE
    )
    if m2:
        result["lit_volume"] = int(m2.group(1).replace(",", ""))
        result["lit_pct"] = float(m2.group(2))
        if "off_exchange_volume" in result:
            result["total_volume"] = result["off_exchange_volume"] + result["lit_volume"]

    # Parse 30d avg: "Off Exchange & Dark Pool volume has been 39.83%"
    m3 = re.search(
        r"Off\s+Exchange\s+&?\s*Dark\s+Pool\s+volume\s+has\s+been\s+([\d.]+)%",
        text, re.IGNORECASE
    )
    if m3:
        result["avg_off_exchange_30d"] = float(m3.group(1))
        result["avg_lit_30d"] = round(100 - result["avg_off_exchange_30d"], 2)

    # Parse exchange breakdown table
    breakdown = []
    # Find table with exchange data
    table_matches = re.findall(
        r'<tr><td[^>]*class="[^"]*"[^>]*>(NYSE\s+Arca|Nasdaq\s+GSM|Cboe\s+\w+|NYSE\s*\w*|IEX|CHX|MEMX'
        r'|Nasdaq\s+PHLX|Cboe\s+\w+|MIAX\s+Pearl|Nasdaq\s+BX|NYSE\s+American|NYSE\s+National'
        r'|24X\s+National|LTSE|Off\s+Exchange)</td>'
        r'\s*<td[^>]*>([\d.]+)</td>'
        r'\s*<td[^>]*>([\d,]+)</td>'
        r'\s*<td[^>]*>([\d.]+)</td></tr>',
        text
    )
    for tm in table_matches:
        name = tm[0].strip()
        day_pct = float(tm[1])
        vol_raw = tm[2].replace(",", "")
        avg_pct = float(tm[3])
        breakdown.append({
            "exchange": name,
            "volume": int(vol_raw),
            "day_pct": day_pct,
            "avg_pct": avg_pct,
        })

    if breakdown:
        result["exchange_breakdown"] = breakdown

    result["signal"] = _derive_signal(result)
    logger.info("DarkPool [%s]: DP=%.1f%% Lit=%.1f%% 30dAvg=%.1f%% Signal=%s",
                ticker,
                result.get("off_exchange_pct", 0),
                result.get("lit_pct", 0),
                result.get("avg_off_exchange_30d", 0),
                result.get("signal", "?"))
    return result


def _derive_signal(data: dict) -> str:
    dp = data.get("off_exchange_pct", 0)
    avg = data.get("avg_off_exchange_30d", 0)
    if avg == 0:
        return "NEUTRAL"
    diff = dp - avg
    if diff > 10:
        return "BULLISH"
    if diff > 3:
        return "SLIGHTLY_BULLISH"
    if diff < -10:
        return "BEARISH"
    if diff < -3:
        return "SLIGHTLY_BEARISH"
    return "NEUTRAL"
