"""
衍生品数据抓取器
=================
尝试从公开源获取:
  - VIX 期限结构 (term structure)
  - Put/Call Ratio (CBOE 公开数据)

数据源:
  - CBOE VIX 期货: https://www.cboe.com/us/futures/market_statistics/vix/  (可能 JS 渲染)
  - CBOE Put/Call: https://www.cboe.com/us/options/market_statistics/        (可能 JS 渲染)
  - BarChart VIX:   https://www.barchart.com/stocks/quotes/$VIX/             (JS 渲染)

注意: 这些数据源大多数依赖 JS 渲染或付费 API，web_fetch 可获取的数据有限。
      在无法获取时，返回 None 并标记 error。
"""

import logging
from typing import Optional

import requests

from config import REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


def get_vix_term_structure() -> Optional[dict]:
    """
    尝试获取 VIX 期限结构。

    方案: CBOE 公开 CSV — https://www.cboe.com/us/futures/market_statistics/vix/
    （通常 JS 渲染，可能不可用）
    备选: 从 Yahoo Finance 获取 VIX 期货连续合约
      ^VX1=F  (近月), ^VX2=F (次月), /VX (连续)
    """
    result = {"spot": None, "front_month": None, "next_month": None, "backwardation": None, "source": None, "error": None}

    try:
        # 尝试获取 VIX 近月和次月期货
        resp = requests.get(
            "https://www.cboe.com/",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=REQUEST_TIMEOUT,
        )
        # 无法直接获取，尝试 BarChart 非 JS 版本
    except Exception:
        pass

    # 通过 Yahoo Finance 获取 VIX 三个月内的价格差异
    # （实际 VIX spot 已在 macro 中获取）
    # 这里标记为无法获取精确 term structure
    result["error"] = (
        "CBOE VIX term structure 依赖 JS 渲染或付费 API，"
        "web_fetch 无法提取精确的 contango/backwardation 数值。"
        "建议: 使用 TradingView 或 Bloomberg 终端手动查看。"
    )
    result["source"] = "attempted: cboe.com → not_fetchable"
    return result


def get_put_call_ratio() -> Optional[dict]:
    """
    尝试获取 CBOE 总 Put/Call Ratio。

    CBOE 公开页面:
      https://www.cboe.com/us/options/market_statistics/

    备选: Barchart, OptionCharts.io（均 JS 渲染）
    最低限度: 从 BarChart HTML meta/script 标签中提取
    """
    result = {"equity_pcr": None, "index_pcr": None, "total_pcr": None, "source": None, "error": None}

    try:
        # Barchart $VIX page — 页面源码可能含有数据
        resp = requests.get(
            "https://www.barchart.com/stocks/quotes/$PCALL/overview",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            # 在页面文本中搜索 "Put/Call Ratio"
            import re
            m = re.search(r'"lastPrice"\s*:\s*"?([\d.]+)"?', resp.text)
            if m:
                ratio = float(m.group(1))
                result["total_pcr"] = ratio
                result["source"] = "barchart.com (script data)"
                result["error"] = None
                return result
    except Exception:
        pass

    result["error"] = (
        "CBOE Put/Call Ratio 公开页为 JS 渲染，"
        "BarChart/OptionCharts 同样受限。"
        "web_fetch 仅可尝试从 BarChart script 标签中提取，但成功率有限。"
    )
    result["source"] = "attempted: cboe.com, barchart.com → not_fetchable"
    return result
