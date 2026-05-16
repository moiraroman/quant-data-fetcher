# Quant Data Fetcher — 产品设计文档 v2.0

> **产品定位**: 零 API Key、全自动、免费数据驱动的美股量化分析数据抓取平台
> **设计哲学**: 数据获取与数据分析完全解耦。抓取层只负责数据供应，分析层独立消费。

---

## 1. 产品概述 (Product Overview)

| 项 | 值 |
|----|-----|
| **产品名称** | Quant Data Fetcher |
| **版本** | 2.0 |
| **核心价值** | 免费美股量化数据全自动抓取，零 API Key |
| **目标用户** | 个人量化交易者、美股投资者 |
| **运行环境** | Windows / macOS / Linux, Python 3.11+ |
| **技术栈** | Python (Flask) + Vanilla HTML/CSS/JS |

### 设计原则

1. **零付费依赖**: 所有数据源均可免费获取，无 API Key 要求
2. **解耦架构**: 数据抓取与数据分析严格分离
3. **容错优先**: 任何单一 Fetcher 失败不影响整体数据输出
4. **双模式**: Web Dashboard (实时监控) + CLI (批量导出)
5. **完整度透明**: 每次抓取报告数据完整度及不可获取项

---

## 2. 数据架构 (Data Architecture)

### 2.1 数据分层

```
Layer 1 — 实时 (秒级):    Yahoo Finance 行情价格 / VIX / DXY / US10Y / GOLD / HYG / JNK
Layer 2 — 日更 (交易时段): Finviz 技术指标 RSI / ATR / SMA% / 多周期收益率
Layer 3 — 日更 (非实时):   CNN Fear & Greed / ChartExchange Dark Pool / Market Breadth / Sector Performance
Layer 4 — 周更:            AAII Sentiment / CFTC COT
Layer 5 — 分钟-小时:        MarketWatch 交叉验证价格 / FRED VIX/TIPS/P-C / 经济日历
Layer 6 — 计算层 (无需抓取): VPVR from OHLCV / SPY vs RSP 差价 / SPY AUM 推断
```

### 2.2 数据源矩阵

| # | 数据项 | 数据源 | 频率 | 方式 | 延迟 | Fetcher | 状态 |
|---|--------|--------|------|------|------|---------|------|
| 1 | 实时行情 (SPY/GDXU/SOXX) | Yahoo Finance v7 | 实时 | JSON API | ~1s | yahoo_fetcher | ✅ |
| 2 | 双源交叉验证 | MarketWatch | 实时 | HTML BS4 | ~1s | marketwatch_fetcher | ✅ |
| 3 | 美东时间 | time.is | 实时 | HTML | ~1s | time_fetcher | ✅ |
| 4 | 技术指标 (RSI/ATR/SMA%) | Finviz | 日更 | HTML BS4 | ~15min | finviz_fetcher | ✅ |
| 5 | MA50/MA200/Beta | Yahoo Finance v8 | 日更 | JSON | ~1s | yahoo_fetcher | ✅ |
| 6 | VIX / DXY / US10Y / GOLD | Yahoo Finance | 实时 | JSON | ~1s | yahoo_fetcher | ✅ |
| 7 | 信用债 (HYG/JNK) | Yahoo Finance | 实时 | JSON | ~1s | yahoo_fetcher | ✅ |
| 8 | CNN Fear & Greed | CNN JSON | ~10min | JSON API | ~10min | cnn_sentiment | ✅ |
| 9 | AAII Sentiment | AAII 公开页 | 周更 | BS4 HTML | 每周 | aaii_fetcher | ✅ |
| 10 | FRED VIX/TIPS/P-C | FRED CSV | 日更 | CSV | T+1 | fred_fetcher | ✅ |
| 11 | Dark Pool / Off-Exchange | ChartExchange | 日更 | BS4 HTML | ~15min | dark_pool | ✅ |
| 12 | CFTC COT | CFTC CSV | 周更 | CSV(zip) | 周+3d | cftc_cot | ✅ |
| 13 | Market Breadth (A/D) | Yahoo + FRED | 日更 | JSON/CSV | T+1 | market_breadth | ✅ |
| 14 | Sector Performance | Yahoo v7 | 日更 | JSON | ~1s | market_breadth | ✅ |
| 15 | VIX Term Structure | CBOE options | 日更 | HTML | ~1s | options_fetcher | ✅ |
| 16 | Put/Call Ratio | CBOE + FRED | 日更 | CSV | T+1 | options_fetcher | ✅ |
| 17 | 经济日历 | 推算 + MarketWatch | — | 计算 | — | econ_calendar | ✅ |
| — | GEX (Gamma Exposure) | OptionsGEX/FlashAlpha | 实时 | Playwright JS | ~1s | — | ❌ Playwright |
| — | Max Pain | maximum-pain.com | 日更 | Playwright JS | ~1s | — | ❌ Playwright |
| — | ETF Flows (精确值) | Nasdaq ETFF | 日更 | 付费API | T+1 | — | ❌ 付费 |
| — | VPVR | 计算 | — | numpy | — | — | 🟢 Plan |

### 2.3 数据流

```
┌──────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│ 13 Fetchers  │───>│  app.py (Flask)   │───>│  Web Dashboard       │
│              │    │  _build_data()    │    │  GET /api/data       │
│ yahoo/ finviz│    │  聚合 + 标准化     │    │  Auto-refresh 60s    │
│ cnn/ fred    │    │  60s TTL Cache    │    │                      │
│ aaii/ dark_p │    │                    │    ├─────────────────────┤
│ cftc_cot     │    │  /api/refresh      │    │  终端用户             │
│ market_bread │    │  强制刷新           │    │  (分析消费层)         │
│ time/ mw     │    │  /api/health       │    │                      │
│ options/ cal │    │  健康检查           │    │                      │
└──────────────┘    └──────────────────┘    └─────────────────────┘

┌──────────────┐
│ fetch_all.py │───> JSON 文件 ──> 分析引擎 (独立消费)
│ CLI 批量导出  │    --output data.json
└──────────────┘
```

---

## 3. 功能模块

### 3.1 Backend — Flask API (app.py)

**端点:**

| 方法 | 路径 | 说明 | 缓存 |
|------|------|------|------|
| GET | `/` | Web Dashboard HTML | 否 |
| GET | `/api/data` | 全部数据 JSON | 60s |
| GET | `/api/refresh` | 强制刷新 JSON | 不命中 |
| GET | `/api/health` | 健康检查 | 否 |

**`/api/data` 响应结构:**

```json
{
  "meta": {
    "timestamp": "2026-05-07T01:30:00Z",
    "fetch_seconds": 4.2,
    "errors": [],
    "data_sources": [
      "yahoo", "finviz", "cnn", "fred",
      "aaii", "dark_pool", "cftc_cot",
      "market_breadth", "sectors"
    ],
    "cache_hit": false
  },
  "tickers": { "SPY": {...}, "GDXU": {...}, "SOXX": {...} },
  "finviz": { "SPY": { "rsi_14": 71.1, ... }, ... },
  "macro": { "VIX": {...}, "DXY": {...}, "US10Y": {...}, "GOLD": {...} },
  "sentiment": { "cnn_fear_greed": { "score": 66, "rating": "Greed" } },
  "fred": { "VIX": { "latest_value": 17.41 }, "TIPS": {...}, "P/C": {...} },
  "aaii": { "date": "Apr 29", "bullish": 38.1, "bearish": 39.7, ... },
  "dark_pool": { "SPY": { "off_exchange_pct": 32.6, ... } },
  "cftc_cot": { "138741": {...} },
  "market_breadth": { "signal": "NEUTRAL", "advance_ratio": 0.52 },
  "sectors": { "XLK": {...}, "XLU": {...} }
}
```

### 3.2 Fetcher 模块 (逐一说明)

| Fetcher | 文件 | 输入 | 输出 | 容错 |
|---------|------|------|------|------|
| YahooFetcher | `yahoo_fetcher.py` | Ticker list | 报价 dict (价格/量/MA/Beta/NAV) | 网络异常 → None |
| FinvizFetcher | `finviz_fetcher.py` | Ticker | Tech dict (RSI/ATR/SMA%/性能) | HTML 异常 → {} |
| CNN Sentiment | `cnn_sentiment.py` | — | {score, rating, prev_*} | JSON 异常 → None |
| FRED | `fred_fetcher.py` | Series IDs | {series: {latest_value, latest_date}} | CSV 异常 → {} |
| Time | `time_fetcher.py` | — | {edt_datetime, session_label} | — |
| MarketWatch | `marketwatch_fetcher.py` | Ticker | {price, change_pct, volume} | 精确度 2% 警告 |
| Options | `options_fetcher.py` | — | {vix_term, put_call_ratio} | — |
| Calendar | `econ_calendar.py` | — | Event list | — |
| **AAII** ⭐ | `aaii_fetcher.py` | — | {bullish, neutral, bearish, spread} | HTML → None |
| **Dark Pool** ⭐ | `dark_pool.py` | Ticker | {off_exchange_pct, lit_pct, breakdown} | Regex → None |
| **CFTC COT** ⭐ | `cftc_cot.py` | Commodity code(s) | {asset_manager, leveraged_fund, dealer} | CSV → None |
| **Breadth** ⭐ | `market_breadth.py` | — | {advance_decline, signal} | — |
| **Sectors** ⭐ | `market_breadth.py` | — | {XLK: {name, change_pct}, ...} | — |

### 3.3 Web Dashboard 分区

| 区域 | 数据来源 | 更新 |
|------|---------|------|
| Header | meta.timestamp, meta.cache_hit | 每次 fetch |
| Ticker Cards | tickers + finviz RSI badge | 每次 fetch |
| Technical Table | finviz (RSI/ATR/SMA/W/M/YTD) | 每次 fetch |
| Macro Cards | macro (VIX/DXY/US10Y/GOLD) + credit (HYG/JNK) + fred | 每次 fetch |
| Sentiment Panel | sentiment.cnn_fear_greed (gauge) + aaii (bars) | 每次 fetch |
| Dark Pool Panel | dark_pool (DP% / Lit% / signal) | 每次 fetch |
| COT Table | cftc_cot (AM vs LF Net) | 每次 fetch |
| Breadth Panel | market_breadth (signal + A/D ratio) | 每次 fetch |
| Sector List | sectors (11 GICS sectors, ranked by % change) | 每次 fetch |
| Error Log | meta.errors (collapsible, red) | 每次 fetch |

### 3.4 CLI (fetch_all.py)

```
Usage:
  python fetch_all.py                        # 抓取 + 摘要 + stdout JSON
  python fetch_all.py --output data.json     # 保存到文件
  python fetch_all.py --quiet                # 仅 stdout JSON
  python fetch_all.py --summary-only         # 仅终端摘要
```

输出: 全 13 个数据类别的统一 JSON。

---

## 4. Web UI 设计规范

### 4.1 页面结构

```
┌─────────────────────────────────────────────┐
│  HEADER: Logo | Timestamp | Cache Badge | Refresh │
├─────────────────────────────────────────────┤
│  TICKER CARDS: [SPY] [GDXU] [SOXX]         │
├─────────────────────────────────────────────┤
│  TECHNICAL TABLE (RSI/ATR/SMA%)              │
├──────────────────┬──────────────────────────┤
│  MACRO CARDS     │  SENTIMENT (CNN + AAII)   │
│  VIX/DXY/US10Y/  │  Gauge + BullBear Bars    │
│  GOLD + HYG/JNK  │                          │
├──────────────────┴──────────────────────────┤
│  DARK POOL PANEL (SPY/GDXU/SOXX)             │
├─────────────────────────────────────────────┤
│  CFTC COT TABLE                               │
├──────────────────┬──────────────────────────┤
│  MARKET BREADTH   │  SECTOR PERFORMANCE       │
│  Signal + A/D    │  (11 sectors, ranked)     │
├──────────────────┴──────────────────────────┤
│  ERROR LOG (collapsible, red)                │
└─────────────────────────────────────────────┘
```

### 4.2 配色方案

| Role | Hex | Usage |
|------|-----|-------|
| **Background Primary** | `#0a0e17` | Body background |
| **Background Secondary** | `#131a2b` | Section cards |
| **Card Background** | `#182033` | Inner cards / table rows |
| **Border** | `#1e2d47` | All borders |
| **Text Primary** | `#e2e8f0` | Main text |
| **Text Secondary** | `#94a3b8` | Labels |
| **Text Muted** | `#64748b` | Meta info |
| **Accent Green (Up)** | `#00d4aa` | Positive values |
| **Accent Red (Down/Warn)** | `#ff4757` | Negative / overbought |
| **Accent Blue (Neutral)** | `#5b9bd5` | Headers / links |
| **Accent Yellow (Neutral)** | `#f0c040` | Neutral sentiment |

### 4.3 交互规范

- **Auto-refresh**: 每 60 秒自动 GET /api/data
- **Force Refresh**: 点击按钮 → GET /api/refresh (强制绕过缓存)
- **Cache Badge**: 绿色 Cached (命中) / 黄色 Fresh (未命中)
- **RSI Badge**: 70+ (红) / 30- (绿) / 其余 (蓝)
- **Error Log**: 折叠展开，红色 Console 字体
- **Loading**: 骨架屏 (skeleton-card shimmer) 在数据未到前

### 4.4 响应式 (Responsive)

- Desktop: 1400px max, full layout
- Tablet: 2-col → 1-col stacking
- Mobile: Card grid → 1-col, tables → scrollable

---

## 5. 系统架构

```
quant_data_fetcher/
├── app.py              # Flask 主程序 (API + 路由)
├── fetch_all.py        # CLI 全量抓取脚本
├── config.py           # 全局配置
├── requirements.txt    # Python 依赖
├── fetchers/           # 13 个数据源模块
│   ├── __init__.py
│   ├── yahoo_fetcher.py       # Yahoo Finance (JSON)
│   ├── finviz_fetcher.py      # Finviz 技术指标 (HTML BS4)
│   ├── cnn_sentiment.py       # CNN Fear & Greed (JSON)
│   ├── fred_fetcher.py        # FRED 经济数据 (CSV)
│   ├── time_fetcher.py        # 美东时间 (HTML)
│   ├── marketwatch_fetcher.py # MarketWatch 验证 (HTML BS4)
│   ├── options_fetcher.py     # VIX/P-C (HTML/JSON)
│   ├── econ_calendar.py       # 经济日历 (计算)
│   ├── aaii_fetcher.py        # AAII 情绪 ⭐ NEW (BS4)
│   ├── dark_pool.py           # 暗池数据 ⭐ NEW (BS4)
│   ├── cftc_cot.py            # COT 持仓 ⭐ NEW (CSV)
│   └── market_breadth.py      # 市场宽度 ⭐ NEW (JSON+CSV)
├── templates/
│   └── index.html     # Web Dashboard HTML (dark theme)
├── static/
│   ├── style.css      # Dashboard 样式 (CSS Grid + Custom Properties)
│   └── app.js         # Dashboard 逻辑 (Vanilla JS fetch)
├── PRODUCT_DESIGN.md  # 本文档
├── README.md
├── DATA_SOURCE_ANALYSIS.md
└── PAYWALL_ALTERNATIVES.md
```

**数据流:**
```
Fetcher.__init__()  → get_quotes() / get_technicals()
         ↓
  _build_data()  →  聚合 (tickers+finviz+sentiment+dark_pool+cot+breadth+sectors)
         ↓
  Flask JSON  →  getElementById.forEach( render*() )
         ↓
  Web UI 渲染
```

**并发模型:** 顺序执行 (Yahoo crumb + Finviz 间隔 1s)，每个 Fetcher 独立 errors 收集。

---

## 6. 数据完整度

### 当前完整度: **85%**

| Layer | 数据类 | #Fetcher | 获取 |
|-------|--------|----------|------|
| L1 — 行情 | Price + Volume + Macro + Credit | 1 | ✅ |
| L2 — 技术 | RSI/ATR/SMA%/MA/Beta | 2 | ✅ |
| L3 — 情绪 | CNN + AAII + Dark Pool + Breadth | 4 | ✅ |
| L4 — 机构 | CFTC COT + Sector | 2 | ✅ |
| L5 — 衍生品 | VIX Term + P/C Ratio | 2 | ✅ |
| L6 — 日历 | Econ Calendar | 1 | ✅ |

### 不可获取 (缺口 ~15%)

| 数据 | 原因 | Plan |
|------|------|------|
| GEX (Gamma Exposure) | JS HTML 渲染 | Phase 2: Playwright (OptionsGEX / FlashAlpha) |
| Max Pain | JS HTML 渲染 | Phase 2: Playwright (maximum-pain.com / optioncharts.io) |
| ETF Flows (精确 Creation/Redemption) | 商业数据库 | Nasdaq ETFF 免费层验证 |
| VIX Term (实时曲线) | vixcentral.com JS渲染 | CBOE 官方 + Playwright |
| VPVR | 需 OHLCV 计算 | 后续加入 numpy 计算 |

---

## 7. 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| Runtime | Python 3 | 3.11.9 |
| Web Server | Flask | 3.1.3 |
| HTTP | requests | 2.33.1 |
| HTML Parse | beautifulsoup4 | 4.14.3 |
| CSV | csv (stdlib) | — |
| ZIP | zipfile (stdlib) | — |
| JSON | json (stdlib) | — |
| Frontend | HTML5 + CSS3 + ES6 | (Vanilla, no frameworks) |
| Caching | threading.Lock + dict | 60s TTL |

**零依赖项:**
- 无 npm 依赖
- 无外部 CSS/JS CDN
- 无数据库
- 零 API Key

---

## 8. 部署指南

### Requirements

```
Flask>=3.0
requests>=2.28
beautifulsoup4>=4.12
```

### 安装

```bash
cd quant_data_fetcher
pip install -r requirements.txt
```

### 运行 Web Dashboard

```bash
python app.py
# → http://127.0.0.1:5050
```

### 命令行批量导出

```bash
python fetch_all.py --output data.json
```

### 一键启动 (Windows)

创建 `run.bat`:
```bat
@echo off
cd /d C:\Users\MAOUOTU\.qclaw\workspace-agent-4c3d0311\quant_data_fetcher
start "" http://127.0.0.1:5050
python app.py
```

---

## 9. 未来路线图

| Phase | 功能 | 技术 | 预估 |
|-------|------|------|------|
| **Phase 2** | Playwright 集成 (GEX/Max Pain/VIX Term) | Playwright-stealth | +15% 完整度 → 95% |
| **Phase 3** | 历史 JSON 存储 (YYYY-MM-DD.json) | JSON files | 回溯分析基础 |
| **Phase 4** | SQLite 持久化 | sqlite3 | 历史回顾、回测 |
| **Phase 5** | Nasdaq ETFF API 验证 | requests + API | ETF精确Flows |
| **Phase 6** | VPVR 计算模块 | pandas + numpy | 体积轮廓指标 |
| **Phase 7** | 告警系统 (Discord/Webhook) | requests | RSI超买/暗池激增 |
| **Phase 8** | 分析引擎接入 | Python SDK | 连接量化分析层 |
| **Phase 9** | Docker 部署 | Dockerfile | 生产级部署 |
| **Phase 10** | 移动端 UI 优化 | Responsive Grid | 手机Dashboard |

---

## 10. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| **v2.0** | 2026-05-07 | 新增 5 个 Fetcher (AAII/DarkPool/CFTC/Sectors/Breadth)；Dashboard 全面重写 (Dark Theme)；完整度 85% |
| v1.0 | 2026-05-05 | 初始 7 个 Fetcher (Yahoo/Finviz/CNN/FRED/Time/MW/Options)；基础 Web UI |
