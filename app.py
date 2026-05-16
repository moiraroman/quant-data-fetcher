"""
Quant Data Fetcher — Flask 主程序
===================================
后端 API 层：整合所有 Fetcher，暴露 RESTful 接口供前端消费。

数据流:
    前端 GET /api/data
      → 检查缓存 (60s TTL)
      → 命中 → 直接返回
      → 未命中 → 并发抓取 Yahoo + Finviz + CNN + FRED
                  + AAII + Dark Pool + CFTC COT + Market Breadth + Sectors
                → 聚合 → 缓存 → 返回

端点:
    GET  /                  → 加载 Web UI
    GET  /api/data          → 获取全部数据 (JSON)
    GET  /api/refresh       → 强制刷新 + 返回全部数据
    GET  /api/health        → 健康检查
"""

import logging
import time
import threading
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template
from flask_cors import CORS

from config import (
    TICKERS,
    MACRO_SYMBOLS,
    CREDIT_SYMBOLS,
    CACHE_TTL_SECONDS,
    FLASK_HOST,
    FLASK_PORT,
    FLASK_DEBUG,
)
from fetchers.yahoo_fetcher import YahooFetcher
from fetchers.finviz_fetcher import FinvizFetcher
from fetchers.cnn_sentiment import get_fear_greed
from fetchers.fred_fetcher import get_all_fred
from fetchers.aaii_fetcher import get_aaii_sentiment
from fetchers.dark_pool import get_dark_pool_summary
from fetchers.cftc_cot import get_cot_all
from fetchers.market_breadth import get_market_breadth, get_sector_performance
from fetchers.historical_prices import get_historical_prices
from indicator_scorer import score_universe

# ---- Logging ----------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("quant-data-fetcher")

# ---- Flask App --------------------------------------------------------------
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# ---- Fetcher 实例（单例）-------------------------------------------------
yahoo = YahooFetcher()
finviz = FinvizFetcher()

# ---- Dark Pool tickers ------------------------------------------------------
DARK_POOL_TICKERS = ["SPY", "GDXU", "SOXX"]

# ---- 简易 TTL Cache ---------------------------------------------------------
_cache: dict = {}
_cache_at: float = 0.0
_cache_lock = threading.Lock()


def _is_cache_fresh() -> bool:
    return (time.time() - _cache_at) < CACHE_TTL_SECONDS


def _build_data() -> dict:
    """
    核心数据聚合函数。
    依次从所有数据源拉取，合并为统一结构。
    """
    started = time.time()
    errors: list[str] = []
    timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ---- 1. Yahoo Finance: 主行情 + 宏观 -------------------------------
    ticker_data: dict[str, dict] = {}
    try:
        all_symbols = TICKERS + list(MACRO_SYMBOLS.keys()) + CREDIT_SYMBOLS
        raw_quotes = yahoo.get_quotes(all_symbols)

        # 按 symbol 分组
        quote_by_sym = {q.get("symbol", ""): q for q in raw_quotes}

        for ticker in TICKERS:
            q = quote_by_sym.get(ticker)
            if q:
                ticker_data[ticker] = _normalize_quote(q, ticker)
            else:
                ticker_data[ticker] = {"symbol": ticker, "error": "no_data"}
                errors.append(f"Yahoo: {ticker} 无数据")

        macro_raw = {}
        for sym, name in MACRO_SYMBOLS.items():
            q = quote_by_sym.get(sym)
            macro_raw[name] = _normalize_quote(q, name) if q else None
            if q is None:
                errors.append(f"Yahoo: {name} 无数据")

        # 信用债 (HYG, JNK)
        for sym in CREDIT_SYMBOLS:
            q = quote_by_sym.get(sym)
            macro_raw[sym] = _normalize_quote(q, sym) if q else None
    except Exception as exc:
        logger.exception("Yahoo fetch error")
        errors.append(f"Yahoo: {exc}")

    # ---- 2. Finviz: 技术指标 ----------------------------------------------
    finviz_data: dict[str, dict] = {}
    for ticker in TICKERS:
        try:
            tech = finviz.get_technicals(ticker)
            if tech:
                finviz_data[ticker] = tech
            else:
                errors.append(f"Finviz: {ticker} 无数据")
        except Exception as exc:
            logger.warning("Finviz %s error: %s", ticker, exc)
            errors.append(f"Finviz: {ticker} -> {exc}")

    # ---- 3. CNN Fear & Greed ---------------------------------------------
    fear_greed = None
    try:
        fear_greed = get_fear_greed()
        if fear_greed is None:
            errors.append("CNN Fear & Greed: 无数据")
    except Exception as exc:
        logger.warning("CNN error: %s", exc)
        errors.append(f"CNN: {exc}")

    # ---- 4. FRED ---------------------------------------------------------
    fred_data = {}
    try:
        fred_data = get_all_fred()
        if not fred_data:
            errors.append("FRED: 无数据")
    except Exception as exc:
        logger.warning("FRED error: %s", exc)
        errors.append(f"FRED: {exc}")

    # ---- 5. AAII Sentiment -----------------------------------------------
    aaii_data = None
    try:
        aaii_data = get_aaii_sentiment()
        if aaii_data is None:
            errors.append("AAII: 无数据")
    except Exception as exc:
        logger.warning("AAII error: %s", exc)
        errors.append(f"AAII: {exc}")

    # ---- 6. Dark Pool (SPY, GDXU, SOXX) ----------------------------------
    dark_pool_data: dict[str, dict] = {}
    for dp_ticker in DARK_POOL_TICKERS:
        try:
            dp_summary = get_dark_pool_summary(dp_ticker)
            if dp_summary:
                dark_pool_data[dp_ticker] = dp_summary
            else:
                errors.append(f"Dark Pool: {dp_ticker} 无数据")
        except Exception as exc:
            logger.warning("Dark Pool %s error: %s", dp_ticker, exc)
            errors.append(f"Dark Pool: {dp_ticker} -> {exc}")

    # ---- 7. CFTC COT -----------------------------------------------------
    cot_data = {}
    try:
        cot_data = get_cot_all()
        if not cot_data:
            errors.append("CFTC COT: 无数据")
    except Exception as exc:
        logger.warning("CFTC COT error: %s", exc)
        errors.append(f"CFTC COT: {exc}")

    # ---- 8. Market Breadth -----------------------------------------------
    breadth_data = None
    try:
        breadth_data = get_market_breadth()
        if breadth_data is None:
            errors.append("Market Breadth: 无数据")
    except Exception as exc:
        logger.warning("Market Breadth error: %s", exc)
        errors.append(f"Market Breadth: {exc}")

    # ---- 9. Sector Performance -------------------------------------------
    sectors_data = {}
    try:
        sectors_data = get_sector_performance()
        if not sectors_data:
            errors.append("Sectors: 无数据")
    except Exception as exc:
        logger.warning("Sectors error: %s", exc)
        errors.append(f"Sectors: {exc}")

    # ---- 10. Historical 30-Day OHLCV ----------------------------------
    historical_data: dict[str, list] = {}
    for ticker in TICKERS:
        try:
            bars = get_historical_prices(yahoo, ticker, days=30)
            if bars:
                historical_data[ticker] = bars
            else:
                errors.append(f"Historical: {ticker} 无数据")
        except Exception as exc:
            logger.warning("Historical %s error: %s", ticker, exc)
            errors.append(f"Historical: {ticker} -> {exc}")

    # ---- 聚合 ------------------------------------------------------------
    elapsed = round(time.time() - started, 2)

    # ---- 先组装基础数据，再做评分 (因为评分引用基础数据) -----------------
    result = {
        "meta": {
            "timestamp": timestamp_utc,
            "fetch_seconds": elapsed,
            "errors": errors,
            "cache_ttl_seconds": CACHE_TTL_SECONDS,
            "data_sources": [
                "yahoo",
                "finviz",
                "cnn",
                "fred",
                "aaii",
                "dark_pool",
                "cftc_cot",
                "market_breadth",
                "sectors",
                "historical",
            ],
        },
        "tickers": ticker_data,
        "finviz": finviz_data,
        "macro": macro_raw,
        "sentiment": fear_greed,
        "fred": fred_data,
        "aaii": aaii_data,
        "dark_pool": dark_pool_data,
        "cftc_cot": cot_data,
        "market_breadth": breadth_data,
        "sectors": sectors_data,
        "historical_prices": historical_data,
    }

    # ---- 10. AI 评分 ----------------------------------------------------
    try:
        result["scores"] = score_universe(result)
    except Exception as exc:
        logger.warning("Scoring error: %s", exc)
        errors.append(f"Scoring: {exc}")
        result["scores"] = {"error": str(exc)}

    return result


def _normalize_quote(q: dict, label: str) -> dict:
    """将 Yahoo raw quote 规范化为前端友好的结构。"""
    if q is None:
        return None
    return {
        "symbol": q.get("symbol", label),
        "name": q.get("shortName") or q.get("longName", label),
        "price": q.get("regularMarketPrice"),
        "change": q.get("regularMarketChange"),
        "change_pct": q.get("regularMarketChangePercent"),
        "day_high": q.get("regularMarketDayHigh"),
        "day_low": q.get("regularMarketDayLow"),
        "prev_close": q.get("regularMarketPreviousClose"),
        "week52_high": q.get("fiftyTwoWeekHigh"),
        "week52_low": q.get("fiftyTwoWeekLow"),
        "volume": q.get("regularMarketVolume"),
        "avg_volume": q.get("averageDailyVolume3Month"),
        "ma_50": q.get("fiftyDayAverage"),
        "ma_200": q.get("twoHundredDayAverage"),
        "beta": q.get("beta"),
        "market_cap": q.get("marketCap"),
        "nav_price": q.get("navPrice"),
        "total_assets": q.get("totalAssets"),
        "market_state": q.get("marketState", "UNKNOWN"),
    }


# ---- Routes ---------------------------------------------------------------


@app.route("/")
def index():
    """加载 Dashboard UI。"""
    return render_template("index.html")


@app.route("/api/data")
def api_data():
    """获取全部聚合数据（含缓存）。"""
    global _cache, _cache_at
    with _cache_lock:
        if _is_cache_fresh() and _cache:
            logger.debug("Cache HIT (age=%.0fs)", time.time() - _cache_at)
            resp = dict(_cache)
            resp["meta"]["cache_hit"] = True
            return jsonify(resp)

    logger.info("Cache MISS — building data...")
    data = _build_data()
    with _cache_lock:
        _cache = data
        _cache_at = time.time()
    data["meta"]["cache_hit"] = False
    return jsonify(data)


@app.route("/api/refresh")
def api_refresh():
    """强制刷新缓存并返回数据。"""
    global _cache, _cache_at
    logger.info("Force refresh...")
    data = _build_data()
    with _cache_lock:
        _cache = data
        _cache_at = time.time()
    data["meta"]["cache_hit"] = False
    return jsonify(data)


@app.route("/api/health")
def api_health():
    """健康检查。"""
    return jsonify({
        "status": "ok",
        "uptime_seconds": round(time.time() - _start_time, 1),
        "cache_age_seconds": round(time.time() - _cache_at, 1) if _cache_at else 0,
        "tickers": TICKERS,
        "macro_symbols": list(MACRO_SYMBOLS.values()),
    })


# ---- 启动 ------------------------------------------------------------------
_start_time = time.time()

if __name__ == "__main__":
    logger.info("Starting Quant Data Fetcher on http://%s:%s", FLASK_HOST, FLASK_PORT)
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
