"""
AAII Sentiment Fetcher
======================
抓取 aaii.com 公开的每周情绪调查结果。
URL: https://www.aaii.com/sentimentsurvey/sent_results
数据: Bullish / Neutral / Bearish 百分比（从1987年至今）
方式: BS4 静态 HTML 抓取，无需 Playwright。
"""

import logging
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("aaii_fetcher")

AAII_URL = "https://www.aaii.com/sentimentsurvey/sent_results"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/132.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.aaii.com/",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Ch-Ua": '"Chromium";v="132", "Google Chrome";v="132"',
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
}
TIMEOUT = 15


def get_aaii_sentiment() -> Optional[dict]:
    """
    获取最新的 AAII 情绪调查数据。
    返回: { date, bullish, neutral, bearish, spread }
    """
    try:
        resp = requests.get(AAII_URL, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # 找到主表 (历史结果表格)
        tables = soup.find_all("table")
        for tbl in tables:
            headers = [th.get_text(strip=True).lower() for th in tbl.find_all("th")]
            # Accept "bullish" or "Bullish"
            if "bullish" in headers or "Bullish" in headers:
                rows = tbl.find_all("tr")
                for row in rows[1:]:  # skip header row
                    cells = row.find_all(["td", "th"])
                    if len(cells) < 4:
                        continue
                    date_str = cells[0].get_text(strip=True)
                    bull = cells[1].get_text(strip=True).replace("%", "")
                    neut = cells[2].get_text(strip=True).replace("%", "")
                    bear = cells[3].get_text(strip=True).replace("%", "")
                    try:
                        bull_f = float(bull)
                        neut_f = float(neut)
                        bear_f = float(bear)
                        spread = round(bull_f - bear_f, 1)
                        result = {
                            "date": date_str,
                            "bullish": bull_f,
                            "neutral": neut_f,
                            "bearish": bear_f,
                            "bull_bear_spread": spread,
                            "source": "aaii.com",
                            "fetched_at": datetime.now().isoformat(),
                        }
                        logger.info("AAII: %s Bull=%s Bear=%s Spread=%s",
                                    date_str, bull, bear, spread)
                        return result
                    except ValueError:
                        continue

        logger.warning("AAII: table with 'bullish' header not found")
        return None

    except Exception as exc:
        logger.error("AAII fetch error: %s", exc)
        return None


def get_aaii_history(days: int = 30) -> list[dict]:
    """
    获取最近 N 天的 AAII 调查历史。
    返回: [{ date, bullish, neutral, bearish }, ...]
    """
    try:
        resp = requests.get(AAII_URL, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        tables = soup.find_all("table")
        for tbl in tables:
            headers = [th.get_text(strip=True).lower() for th in tbl.find_all("th")]
            if "bullish" not in headers and "Bullish" not in headers:
                continue

            for row in tbl.find_all("tr"):
                cells = row.find_all(["td", "th"])
                if len(cells) < 4:
                    continue
                try:
                    date_str = cells[0].get_text(strip=True)
                    bull = float(cells[1].get_text(strip=True).replace("%", ""))
                    neut = float(cells[2].get_text(strip=True).replace("%", ""))
                    bear = float(cells[3].get_text(strip=True).replace("%", ""))
                    results.append({
                        "date": date_str,
                        "bullish": bull,
                        "neutral": neut,
                        "bearish": bear,
                        "bull_bear_spread": round(bull - bear, 1),
                    })
                except (ValueError, IndexError):
                    continue

        logger.info("AAII: 历史数据 %d 条", len(results))
        return results[:days]

    except Exception as exc:
        logger.error("AAII history error: %s", exc)
        return []