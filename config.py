# ============================================================
# Quant Data Fetcher — Configuration v2.0
# ============================================================
# 主分析标的
TICKERS = ["SPY", "GDXU", "SOXX"]

# 宏观指标 (Yahoo Finance 符号)
MACRO_SYMBOLS = {
    "^VIX": "VIX",
    "DX-Y.NYB": "DXY",
    "^TNX": "US10Y",
    "GC=F": "GOLD",
}

# 宏观指标看板 — 需要展示的字段
MACRO_DISPLAY_KEYS = {
    "VIX": ["regularMarketPrice", "regularMarketChange", "regularMarketChangePercent"],
    "DXY": ["regularMarketPrice", "regularMarketChange", "regularMarketChangePercent"],
    "US10Y": ["regularMarketPrice", "regularMarketChange", "regularMarketChangePercent"],
    "GOLD": ["regularMarketPrice", "regularMarketChange", "regularMarketChangePercent"],
}

# ============================================================
# 数据源配置
# ============================================================

# Yahoo Finance
YAHOO_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/132.0.0.0 Safari/537.36"
)
YAHOO_CRUMB_TTL = 300  # crumb 有效期 (秒)

# Finviz
FINVIZ_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/132.0.0.0 Safari/537.36"
)

# CNN Fear & Greed
CNN_FEAR_GREED_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

# FRED (Federal Reserve Economic Data)
FRED_SERIES = {
    "VIXCLS": "VIX",        # CBOE Volatility Index (T-1 close)
    "DFII10": "TIPS",       # 10-Year TIPS (实际收益率 = 真实资金成本)
    "TOTPUTCALL": "P/C",    # CBOE Total Put/Call Ratio (from FRED release 200)
}

# AAII Sentiment
AAII_URL = "https://www.aaii.com/sentimentsurvey/sent_results"

# CFTC Commitments of Traders
CFTC_COT_BASE = "https://www.cftc.gov/dea/futures"
CFTC_COT_SYMBOLS = {
    "ES": "E-mini S&P 500",
    "NQ": "E-mini NASDAQ 100",
}

# ChartExchange Dark Pool
CHARTEXCHANGE_BASE = "https://chartexchange.com/symbol"
DARK_POOL_TICKERS = ["SPY", "QQQ"]  # 可扩展

# Market Breadth
MARKET_BREADTH_SOURCES = {
    "barrons": "https://www.barrons.com/market-data/stocks/markets-diary",
    "wsj": "https://www.wsj.com/market-data/stocks/marketsdiary",
}

# SPY Holdings / Institutional
SPY_HOLDINGS_SOURCES = [
    "https://www.slickcharts.com/symbol/SPY/holdings",
    "https://stockanalysis.com/etf/spy/holdings/",
]

# ============================================================
# 信用债 (High Yield Credit Market)
CREDIT_SYMBOLS = ["HYG", "JNK"]   # 高收益公司债 ETF — 风险偏好指标

# ============================================================
# 衍生品/期权数据（V2 新增）
# ============================================================
# VIX Term Structure — VIX Futures (Yahoo Finance symbols)
VIX_FUTURES_SYMBOLS = {
    "^VIX": "Spot",
    # 近月 VIX Futures = M1, M2 (Yahoo可能支持)
}

# Max Pain (V2 暂用 estimate: 最大 OI strike 集)
MAX_PAIN_SOURCES = {
    "optioncharts": "https://optioncharts.io/options/{ticker}/max-pain",
}

# ============================================================
# 缓存 & 请求
# ============================================================
CACHE_TTL_SECONDS = 60        # 数据缓存时间
REQUEST_TIMEOUT = 15          # HTTP 请求超时 (秒)
FINVIZ_RATE_LIMIT = 1.0       # Finviz 请求间隔 (秒) — 避免被封

# ============================================================
# 服务
# ============================================================
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5050
FLASK_DEBUG = True
