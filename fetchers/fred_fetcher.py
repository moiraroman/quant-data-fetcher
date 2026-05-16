"""
FRED (Federal Reserve Economic Data) 抓取器
=============================================
通过 FRED graph CSV endpoint 获取数据，无需 API Key。

数据源:
    https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES_ID}&cosd=...&coed=...

可获取指标:
    VIXCLS   — CBOE Volatility Index (VIX), daily close
    DFII10   — 10-Year TIPS (Treasury Inflation-Protected Securities) 实际收益率
    DGS10    — 10-Year Treasury Constant Maturity Rate, daily
    DTWEXBGS — Nominal Broad U.S. Dollar Index, daily

注意:
    - FRED 数据有 1 天延迟（T-1 收盘值）
    - 返回标准 CSV (header + rows)
"""

import logging
from typing import Optional

import requests

from config import FRED_SERIES, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


def get_fred_series(series_id: str) -> Optional[dict]:
    """
    获取单个 FRED 序列的最新值。

    返回:
        {
            "series_id": "VIXCLS",
            "label": "VIX",
            "latest_date": "2026-05-04",
            "latest_value": 20.50,
            "unit": "Index",
        }
    """
    # FRED graph CSV endpoint — 无需 API Key，返回最近数据
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    url = (
        f"https://fred.stlouisfed.org/graph/fredgraph.csv"
        f"?id={series_id}&cosd={start_date}&coed={end_date}"
    )
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("FRED fetch %s failed: %s", series_id, exc)
        return None

    lines = resp.text.strip().split("\n")
    if len(lines) < 2:
        logger.warning("FRED %s: no data rows", series_id)
        return None

    # 第一行为 header (observation_date,{series_id})
    # 最后一行为最新数据
    last_line = lines[-1]
    parts = last_line.split(",")
    if len(parts) < 2:
        return None

    date_str = parts[0].strip()
    try:
        value = float(parts[1].strip())
    except (ValueError, IndexError):
        value = None

    # 已知指标的 label/unit 映射
    known = {
        "VIXCLS": ("CBOE Volatility Index", "Index"),
        "DFII10": ("10-Year TIPS Real Yield", "%"),
        "DGS10": ("10-Year Treasury Rate", "%"),
        "DTWEXBGS": ("Trade Weighted USD Index", "Index"),
    }
    label, unit = known.get(series_id, (series_id, ""))

    return {
        "series_id": series_id,
        "label": label,
        "latest_date": date_str,
        "latest_value": value,
        "unit": unit,
    }


def get_all_fred() -> dict[str, dict]:
    """批量获取所有配置的 FRED 序列。"""
    results = {}
    for series_id, name in FRED_SERIES.items():
        data = get_fred_series(series_id)
        if data:
            data["display_name"] = name
            results[name] = data
    return results
