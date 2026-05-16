"""
CNN Fear & Greed Index 抓取器
===============================
直接调用 CNN 公开 JSON API，无需认证。

端点:
    https://production.dataviz.cnn.io/index/fearandgreed/graphdata

返回示例:
{
  "fear_and_greed": {
    "score": 66.6,
    "rating": "greed",           // extreme fear | fear | neutral | greed | extreme greed
    "timestamp": "2026-05-01T23:59:39+00:00",
    "previous_close": 66.6,
    "previous_1_week": 66.0285714285714,
    "previous_1_month": 64.8,
    "previous_1_year": 62.3
  }
}
"""

import logging
from typing import Optional

import requests

from config import CNN_FEAR_GREED_URL, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

# 中文标签
RATING_LABELS = {
    "extreme fear": "极度恐惧",
    "fear": "恐惧",
    "neutral": "中性",
    "greed": "贪婪",
    "extreme greed": "极度贪婪",
}


def get_fear_greed() -> Optional[dict]:
    """
    获取 CNN Fear & Greed 最新数据。

    返回:
        {
            "score": 66.6,
            "rating": "greed",
            "rating_cn": "贪婪",
            "timestamp": "2026-05-01T23:59:39+00:00",
            "previous_close": 66.6,
            "previous_1_week": 66.03,
            "previous_1_month": 64.8,
            "previous_1_year": 62.3,
        }
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/132.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.cnn.com",
            "Referer": "https://www.cnn.com/markets/fear-and-greed",
        }
        resp = requests.get(
            CNN_FEAR_GREED_URL,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        body = resp.json()
        fg = body.get("fear_and_greed", {})
        if not fg:
            logger.warning("CNN Fear & Greed response missing 'fear_and_greed' key")
            return None

        rating = fg.get("rating", "").lower()
        return {
            "score": fg.get("score"),
            "rating": rating,
            "rating_cn": RATING_LABELS.get(rating, rating),
            "timestamp": fg.get("timestamp"),
            "previous_close": fg.get("previous_close"),
            "previous_1_week": fg.get("previous_1_week"),
            "previous_1_month": fg.get("previous_1_month"),
            "previous_1_year": fg.get("previous_1_year"),
        }
    except requests.RequestException as exc:
        logger.warning("CNN Fear & Greed fetch failed: %s", exc)
        return None
    except (ValueError, KeyError) as exc:
        logger.warning("CNN Fear & Greed parse failed: %s", exc)
        return None
