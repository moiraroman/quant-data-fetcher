"""
Indicator Scorer — 利多/利空评分引擎
====================================
对每个指标计算 -100 (极度利空) ~ +100 (极度利多) 的评分，
然后按 AI 判断的权重聚合为各标的总体多空评估。

评分规则基于经典量化分析的逆向思维：
- 超买 → 利空 (均值回归预期)
- 情绪极端贪婪 → 利空 (反向指标)
- 暗池占比高于均值 → 利空 (机构暗度陈仓)
"""

from typing import Optional


# ╔══════════════════════════════════════════════════════════╗
# ║  单指标评分函数                                         ║
# ╚══════════════════════════════════════════════════════════╝

def score_rsi(rsi: Optional[float]) -> Optional[dict]:
    """RSI 评分: 超买利空, 超卖利多"""
    if rsi is None:
        return None
    if rsi >= 80:
        score, bull_pct, bear_pct, detail = -85, 8, 92, "极度超买，回调风险极高"
    elif rsi >= 70:
        score, bull_pct, bear_pct, detail = -55, 23, 77, "超买区域，短期回调压力"
    elif rsi >= 60:
        score, bull_pct, bear_pct, detail = -15, 43, 57, "偏强，但渐近超买"
    elif rsi >= 45:
        score, bull_pct, bear_pct, detail = 15, 57, 43, "中性偏多，动量健康"
    elif rsi >= 30:
        score, bull_pct, bear_pct, detail = 40, 70, 30, "偏弱，接近超卖机会区"
    elif rsi >= 20:
        score, bull_pct, bear_pct, detail = 65, 83, 17, "超卖区域，反弹概率大"
    else:
        score, bull_pct, bear_pct, detail = 90, 95, 5, "极度超卖，强烈反弹信号"
    return {"name": "RSI(14)", "value": rsi, "score": score,
            "bull_pct": bull_pct, "bear_pct": bear_pct, "detail": detail}


def score_sma_pct(pct: Optional[float], period: int, ticker_hint: str = "") -> Optional[dict]:
    """移动平均偏离: 价格高于均线利多, 低于利空。3x 杠杆需考虑均值回归。"""
    if pct is None:
        return None
    is_3x = "3x" in ticker_hint.lower() or ticker_hint in ("GDXU",)
    multiplier = 0.6 if is_3x else 1.0  # 3x 杠杆均值回归更强

    if pct > 15:
        score, bull_pct, bear_pct, detail = int(50 * multiplier), 75, 25, f"SMA{period} 大幅乖离，趋势极强但有均值回归风险"
    elif pct > 8:
        score, bull_pct, bear_pct, detail = int(40 * multiplier), 70, 30, f"SMA{period} 上方运行，多头趋势明确"
    elif pct > 3:
        score, bull_pct, bear_pct, detail = int(25 * multiplier), 63, 37, f"SMA{period} 上方，短期强势"
    elif pct > 0:
        score, bull_pct, bear_pct, detail = int(10 * multiplier), 55, 45, f"SMA{period} 微幅上方，方向不明"
    elif pct > -3:
        score, bull_pct, bear_pct, detail = int(-10 * multiplier), 45, 55, f"SMA{period} 微幅下方，弱势整理"
    elif pct > -8:
        score, bull_pct, bear_pct, detail = int(-25 * multiplier), 37, 63, f"SMA{period} 下方运行，空头占优"
    elif pct > -15:
        score, bull_pct, bear_pct, detail = int(-45 * multiplier), 28, 72, f"SMA{period} 下方，趋势偏空"
    else:
        score, bull_pct, bear_pct, detail = int(-65 * multiplier), 18, 82, f"SMA{period} 大幅乖离，极度弱势"
    return {"name": f"SMA{period}%", "value": pct, "score": score,
            "bull_pct": bull_pct, "bear_pct": bear_pct, "detail": detail}


def score_sma_200_raw_price(price: Optional[float], ma_200: Optional[float]) -> Optional[dict]:
    """价格 vs SMA200 raw: 核心趋势判断"""
    if price is None or ma_200 is None or ma_200 == 0:
        return None
    pct = ((price / ma_200) - 1) * 100
    return score_sma_pct(pct, 200)


def score_vix(vix: Optional[float]) -> Optional[dict]:
    """VIX: 低波利多，高波利空"""
    if vix is None:
        return None
    if vix > 30:
        score, bull_pct, bear_pct, detail = -80, 10, 90, "极高波动，恐慌蔓延"
    elif vix > 25:
        score, bull_pct, bear_pct, detail = -55, 23, 77, "高波动，避险情绪上升"
    elif vix > 20:
        score, bull_pct, bear_pct, detail = -25, 38, 62, "波动偏高，市场不安"
    elif vix > 15:
        score, bull_pct, bear_pct, detail = 15, 57, 43, "正常偏低，市场平稳"
    elif vix > 12:
        score, bull_pct, bear_pct, detail = 40, 70, 30, "低波动，市场自满但健康"
    else:
        score, bull_pct, bear_pct, detail = 55, 78, 22, "极低波动，市场过度自满（警惕黑天鹅）"
    return {"name": "VIX", "value": vix, "score": score,
            "bull_pct": bull_pct, "bear_pct": bear_pct, "detail": detail}


def score_dxy(dxy: Optional[float]) -> Optional[dict]:
    """DXY: 弱美元利多风险资产 (尤其黄金/新兴), 强美元利空"""
    if dxy is None:
        return None
    if dxy > 108:
        score, bull_pct, bear_pct, detail = -35, 33, 67, "美元极强，压制大宗商品与新兴市场"
    elif dxy > 103:
        score, bull_pct, bear_pct, detail = -15, 43, 57, "美元偏强，对黄金/资源股利空"
    elif dxy > 98:
        score, bull_pct, bear_pct, detail = 5, 53, 47, "中性偏弱，商品/新兴获支撑"
    elif dxy > 94:
        score, bull_pct, bear_pct, detail = 25, 63, 37, "美元弱势，利好黄金与风险资产"
    else:
        score, bull_pct, bear_pct, detail = 45, 72, 28, "美元极弱，全面利好大宗商品"
    return {"name": "DXY", "value": dxy, "score": score,
            "bull_pct": bull_pct, "bear_pct": bear_pct, "detail": detail}


def score_us10y(us10y: Optional[float]) -> Optional[dict]:
    """10Y: 利率适中利多成长，过高利空"""
    if us10y is None:
        return None
    if us10y > 5.5:
        score, bull_pct, bear_pct, detail = -60, 20, 80, "高利率压制成长股估值"
    elif us10y > 4.5:
        score, bull_pct, bear_pct, detail = -25, 38, 62, "利率偏高，成长股承压"
    elif us10y > 3.8:
        score, bull_pct, bear_pct, detail = 5, 53, 47, "中性利率，市场可接受"
    elif us10y > 3.0:
        score, bull_pct, bear_pct, detail = 20, 60, 40, "利率偏宽松，利好风险资产"
    else:
        score, bull_pct, bear_pct, detail = 40, 70, 30, "低利率环境，强力支撑估值"
    return {"name": "US10Y", "value": us10y, "score": score,
            "bull_pct": bull_pct, "bear_pct": bear_pct, "detail": detail}


def score_gold(gold: Optional[float], for_ticker: str = "SPY") -> Optional[dict]:
    """黄金: 对 SPY/SOXX 是避险信号(利空), 对 GDXU 是利多"""
    if gold is None:
        return None
    is_gold_miner = for_ticker == "GDXU"

    if gold > 5000:
        raw_score = -40 if not is_gold_miner else 70
    elif gold > 4000:
        raw_score = -20 if not is_gold_miner else 50
    elif gold > 3000:
        raw_score = 0 if not is_gold_miner else 30
    elif gold > 2000:
        raw_score = 15 if not is_gold_miner else 10
    else:
        raw_score = 30 if not is_gold_miner else -20

    if is_gold_miner:
        detail = "金价高位极大利好金矿股" if raw_score > 40 else \
                 "金价利好金矿板块" if raw_score > 0 else "金价低迷压制金矿股"
    else:
        detail = "高位黄金=避险情绪=利空风险资产" if raw_score < 0 else \
                 "黄金温和=风险偏好正常"

    bull_pct = int((raw_score + 100) / 2)
    bear_pct = 100 - bull_pct
    return {"name": "GOLD", "value": gold, "score": raw_score,
            "bull_pct": bull_pct, "bear_pct": bear_pct, "detail": detail}


def score_fear_greed(fg_value: Optional[float]) -> Optional[dict]:
    """CNN F&G: 极端贪婪=反向利空, 极端恐惧=反向利多"""
    if fg_value is None:
        return None
    v = fg_value
    if v > 80:
        score, bull_pct, bear_pct, detail = -75, 13, 87, "极度贪婪，历史顶部信号"
    elif v > 65:
        score, bull_pct, bear_pct, detail = -35, 33, 67, "贪婪区域，追高风险加大"
    elif v > 50:
        score, bull_pct, bear_pct, detail = -5, 48, 52, "中性偏贪婪，正常"
    elif v > 35:
        score, bull_pct, bear_pct, detail = 15, 57, 43, "中性偏恐惧，正常"
    elif v > 20:
        score, bull_pct, bear_pct, detail = 45, 72, 28, "恐惧区域，通常是买点"
    else:
        score, bull_pct, bear_pct, detail = 80, 90, 10, "极度恐惧，历史底部信号，强烈买入"
    return {"name": "CNN F&G", "value": v, "score": score,
            "bull_pct": bull_pct, "bear_pct": bear_pct, "detail": detail}


def score_hyg_jnk(hyg_price: Optional[float], hyg_change_pct: Optional[float],
                  jnk_price: Optional[float], jnk_change_pct: Optional[float]) -> Optional[dict]:
    """信用债: HYG/JNK 走强=风险偏好=利多"""
    changes = [c for c in [hyg_change_pct, jnk_change_pct] if c is not None]
    if not changes:
        return None
    avg_change = sum(changes) / len(changes)

    if avg_change > 1:
        score, bull_pct, bear_pct, detail = 35, 68, 32, "信用债走强，风险偏好高涨"
    elif avg_change > 0.3:
        score, bull_pct, bear_pct, detail = 15, 57, 43, "信用债微涨，风险偏好健康"
    elif avg_change > -0.3:
        score, bull_pct, bear_pct, detail = 0, 50, 50, "信用债持平，中性"
    elif avg_change > -1:
        score, bull_pct, bear_pct, detail = -20, 40, 60, "信用债走弱，风险偏好下降"
    else:
        score, bull_pct, bear_pct, detail = -45, 28, 72, "信用债大跌，信用危机预警"
    return {"name": "HYG/JNK", "value": round(avg_change, 2), "score": score,
            "bull_pct": bull_pct, "bear_pct": bear_pct, "detail": detail}


def score_dark_pool(dp_pct: Optional[float], avg_30d: Optional[float]) -> Optional[dict]:
    """暗池: DP% > 30d均=机构暗度陈仓=利空; DP% < 均=利多"""
    if dp_pct is None or avg_30d is None:
        return None
    diff = dp_pct - avg_30d
    if diff > 10:
        score, bull_pct, bear_pct, detail = -55, 23, 77, f"暗池占比显著高于均值({diff:+.1f}pp)，机构出货"
    elif diff > 5:
        score, bull_pct, bear_pct, detail = -30, 35, 65, f"暗池占比高于均值({diff:+.1f}pp)，偏空"
    elif diff > 0:
        score, bull_pct, bear_pct, detail = -10, 45, 55, f"暗池微高于均值({diff:+.1f}pp)，略偏空"
    elif diff > -5:
        score, bull_pct, bear_pct, detail = 10, 55, 45, f"暗池低于均值({diff:+.1f}pp)，略偏多"
    elif diff > -10:
        score, bull_pct, bear_pct, detail = 30, 65, 35, f"暗池明显低于均值({diff:+.1f}pp)，机构吸筹"
    else:
        score, bull_pct, bear_pct, detail = 50, 75, 25, f"暗池大幅低于均值({diff:+.1f}pp)，强烈吸筹信号"
    return {"name": "Dark Pool", "value": dp_pct, "score": score,
            "bull_pct": bull_pct, "bear_pct": bear_pct, "detail": detail}


def score_market_breadth(breadth: Optional[dict]) -> Optional[dict]:
    """市场宽度: 涨跌比 > 1 利多"""
    if not breadth:
        return None
    ratio = breadth.get("advance_ratio")
    if ratio is None:
        return None
    if ratio > 3:
        score, bull_pct, bear_pct, detail = 60, 80, 20, f"极端强势({ratio:.1f}:1)，全市场普涨"
    elif ratio > 2:
        score, bull_pct, bear_pct, detail = 40, 70, 30, f"强势({ratio:.1f}:1)，多头主导"
    elif ratio > 1.2:
        score, bull_pct, bear_pct, detail = 15, 57, 43, f"偏多({ratio:.1f}:1)"
    elif ratio > 1:
        score, bull_pct, bear_pct, detail = 5, 53, 47, f"微多({ratio:.1f}:1)"
    elif ratio > 0.8:
        score, bull_pct, bear_pct, detail = -5, 47, 53, f"微空({ratio:.1f}:1)"
    elif ratio > 0.5:
        score, bull_pct, bear_pct, detail = -20, 40, 60, f"偏空({ratio:.1f}:1)"
    elif ratio > 0.33:
        score, bull_pct, bear_pct, detail = -40, 30, 70, f"弱势({ratio:.1f}:1)"
    else:
        score, bull_pct, bear_pct, detail = -65, 18, 82, f"极度弱势({ratio:.1f}:1)"
    return {"name": "Market Breadth", "value": ratio, "score": score,
            "bull_pct": bull_pct, "bear_pct": bear_pct, "detail": detail}


def score_sector_rotation(sectors: dict, ticker: str) -> Optional[dict]:
    """板块轮动: Tech领涨利多SOXX, 防御领涨利多SPY但利空SOXX"""
    if not sectors:
        return None
    # 按涨幅排序
    sorted_sec = sorted(sectors.items(), key=lambda x: x[1].get("change_pct", 0) or 0, reverse=True)
    leading = sorted_sec[0][0] if sorted_sec else None
    leading_pct = sorted_sec[0][1].get("change_pct", 0) if sorted_sec else 0

    growth_leaders = {"XLK", "XLY", "XLC"}
    defensive_leaders = {"XLU", "XLP", "XLV"}

    score = 10
    if leading in growth_leaders:
        detail = f"成长股领涨({leading} +{leading_pct:.1f}%)，利好科技/半导体"
        if ticker == "SOXX":
            score = 30
        elif ticker == "SPY":
            score = 20
    elif leading in defensive_leaders:
        detail = f"防御板块领涨({leading} +{leading_pct:.1f}%)，避险信号"
        score = -15
    else:
        detail = f"周期板块领涨({leading} +{leading_pct:.1f}%)，中性偏多"
        score = 10

    bull_pct = int((score + 100) / 2)
    bear_pct = 100 - bull_pct
    return {"name": "Sector Rotation", "value": leading, "score": score,
            "bull_pct": bull_pct, "bear_pct": bear_pct, "detail": detail}


# ╔══════════════════════════════════════════════════════════╗
# ║  标的专属权重 (AI 判断)                                ║
# ╚══════════════════════════════════════════════════════════╝

# 每个标的的指标权重总和 = 100%
# 权重基于: 指标对标的的历史解释力 + 当前市场环境特性

WEIGHTS = {
    "SPY": {
        # 技术面 35% — 大盘依赖趋势
        "RSI(14)": 13,
        "SMA20%": 6,
        "SMA50%": 8,
        "SMA200%": 8,
        # 宏观 25% — 大盘受宏观驱动
        "VIX": 10,
        "DXY": 4,
        "US10Y": 6,
        "GOLD": 5,
        # 情绪 20%
        "CNN F&G": 12,
        "HYG/JNK": 8,
        # 资金 + 宽度 20%
        "Dark Pool": 8,
        "Market Breadth": 8,
        "Sector Rotation": 4,
    },
    "GDXU": {
        # 技术面 25% — 3x杠杆均值回归强
        "RSI(14)": 10,
        "SMA20%": 5,
        "SMA50%": 5,
        "SMA200%": 5,
        # 宏观 45% — 金矿股的核心驱动
        "VIX": 5,
        "DXY": 12,
        "US10Y": 8,
        "GOLD": 20,
        # 情绪 15%
        "CNN F&G": 10,
        "HYG/JNK": 5,
        # 资金 + 宽度 15%
        "Dark Pool": 5,
        "Market Breadth": 6,
        "Sector Rotation": 4,
    },
    "SOXX": {
        # 技术面 30%
        "RSI(14)": 12,
        "SMA20%": 6,
        "SMA50%": 6,
        "SMA200%": 6,
        # 宏观 25% — SOXX 对利率敏感
        "VIX": 6,
        "DXY": 3,
        "US10Y": 10,
        "GOLD": 6,
        # 情绪 20%
        "CNN F&G": 12,
        "HYG/JNK": 8,
        # 资金 + 宽度 20%
        "Dark Pool": 8,
        "Market Breadth": 8,
        "Sector Rotation": 9,
    },
}


# ╔══════════════════════════════════════════════════════════╗
# ║  主评分函数                                            ║
# ╚══════════════════════════════════════════════════════════╝

def classify_signal(weighted_score: float) -> str:
    """将加权分数映射到信号标签"""
    if weighted_score >= 50:
        return "STRONGLY_BULLISH"
    elif weighted_score >= 20:
        return "BULLISH"
    elif weighted_score >= 5:
        return "SLIGHTLY_BULLISH"
    elif weighted_score > -5:
        return "NEUTRAL"
    elif weighted_score > -20:
        return "SLIGHTLY_BEARISH"
    elif weighted_score > -50:
        return "BEARISH"
    else:
        return "STRONGLY_BEARISH"


def score_to_bull_bear(weighted_score: float) -> tuple:
    """将加权分转为利多/利空百分比。
    例: +40 -> 利多 70%, 利空 30%; -30 -> 利多 35%, 利空 65%
    """
    if weighted_score >= 0:
        bullish_pct = int(50 + weighted_score * 0.5)
        bearish_pct = 100 - bullish_pct
    else:
        bearish_pct = int(50 + abs(weighted_score) * 0.5)
        bullish_pct = 100 - bearish_pct
    # clamp
    bullish_pct = max(0, min(100, bullish_pct))
    bearish_pct = max(0, min(100, bearish_pct))
    return bullish_pct, bearish_pct


def score_ticker(ticker: str, data: dict) -> dict:
    """
    对单个标的综合评分。
    
    data = app.py _build_data() 返回的完整结构。
    返回:
        {
            "indicators": [{name, value, score, bull_pct, bear_pct, detail}, ...],
            "weighted_score": -15.3,      # 加权总分
            "bullish_pct": 42,             # 利多%
            "bearish_pct": 58,             # 利空%
            "signal": "SLIGHTLY_BEARISH",  # 信号标签
            "weights_used": {...}
        }
    """
    weights = WEIGHTS.get(ticker, WEIGHTS["SPY"])
    ticker_info = (data.get("tickers") or {}).get(ticker, {})
    finviz = (data.get("finviz") or {}).get(ticker, {})
    macro = data.get("macro") or {}
    dark_pool = (data.get("dark_pool") or {}).get(ticker, {})
    breadth = data.get("market_breadth") or {}
    sectors = data.get("sectors") or {}
    sentiment = data.get("sentiment") or {}

    # 基础值提取
    price = ticker_info.get("price")
    change_pct = ticker_info.get("change_pct")

    rsi = finviz.get("rsi_14")
    sma20 = finviz.get("sma20_pct")
    sma50 = finviz.get("sma50_pct")
    sma200 = finviz.get("sma200_pct")

    vix_price = (macro.get("VIX") or {}).get("price")
    dxy_price = (macro.get("DXY") or {}).get("price")
    us10y_price = (macro.get("US10Y") or {}).get("price")
    gold_price = (macro.get("GOLD") or {}).get("price")

    fg_value = sentiment.get("score") if sentiment else None

    hyg_info = macro.get("HYG", {}) if "HYG" in macro else ticker_info
    jnk_info = macro.get("JNK", {}) if "JNK" in macro else {}
    hyg_change = _safe_get(hyg_info, "change_pct")
    jnk_change = _safe_get(jnk_info, "change_pct")

    dp_pct = dark_pool.get("off_exchange_pct")
    dp_avg = dark_pool.get("avg_off_exchange_30d")

    # ---- 逐指标评分 ----
    indicators = []

    def add(result):
        if result:
            indicators.append(result)

    add(score_rsi(rsi))
    add(score_sma_pct(sma20, 20, ticker))
    add(score_sma_pct(sma50, 50, ticker))
    add(score_sma_pct(sma200, 200, ticker))
    add(score_vix(vix_price))
    add(score_dxy(dxy_price))
    add(score_us10y(us10y_price))
    add(score_gold(gold_price, ticker))
    add(score_fear_greed(fg_value))
    add(score_hyg_jnk(hyg_info.get("price"), hyg_change,
                       jnk_info.get("price"), jnk_change))
    add(score_dark_pool(dp_pct, dp_avg))
    add(score_market_breadth(breadth))
    add(score_sector_rotation(sectors, ticker))

    # ---- 加权聚合 ----
    total_weight = 0.0
    weighted_sum = 0.0
    for ind in indicators:
        name = ind["name"]
        w = weights.get(name, 0)
        if w > 0:
            weighted_sum += ind["score"] * w
            total_weight += w

    weighted_score = round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0
    bullish_pct, bearish_pct = score_to_bull_bear(weighted_score)
    signal = classify_signal(weighted_score)

    return {
        "indicators": indicators,
        "weighted_score": weighted_score,
        "bullish_pct": bullish_pct,
        "bearish_pct": bearish_pct,
        "signal": signal,
        "weights_used": weights,
    }


def score_universe(data: dict) -> dict:
    """对所有标的评分 + 市场环境总分"""
    tickers = ["SPY", "GDXU", "SOXX"]
    results = {}
    for t in tickers:
        results[t] = score_ticker(t, data)

    # 市场环境总分 = SPY 评分 (代表整体市场)
    results["MARKET"] = results["SPY"]

    return results


def _safe_get(d: dict, key: str):
    """安全地从 dict 取值，处理 None"""
    if not d:
        return None
    return d.get(key)


# ╔══════════════════════════════════════════════════════════╗
# ║  测试                                                  ║
# ╚══════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    # 独立测试
    import json
    import sys
    sys.path.insert(0, ".")
    from fetchers.yahoo_fetcher import YahooFetcher
    from fetchers.finviz_fetcher import FinvizFetcher

    y = YahooFetcher()
    f = FinvizFetcher()

    quotes = y.get_quotes(["SPY", "GDXU", "SOXX", "^VIX", "DX-Y.NYB", "^TNX", "GC=F"])
    print("Quotes:", len(quotes))

    tech = f.get_technicals("SPY")
    print("SPY Tech:", tech)

    # Mock minimal data
    mock = {
        "tickers": {"SPY": {"price": quotes[0].get("regularMarketPrice") if quotes else None}},
        "finviz": {"SPY": tech},
        "macro": {},
        "dark_pool": {},
        "market_breadth": {},
        "sectors": {},
        "sentiment": {},
    }
    result = score_ticker("SPY", mock)
    print(json.dumps(result, ensure_ascii=False, indent=2))
