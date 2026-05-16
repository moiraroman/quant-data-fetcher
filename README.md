# Quant Data Fetcher

> 量化数据抓取系统 / クオンタデータ取得システム / Quantitative Data Acquisition System

---

## 中文

### 简介

**Quant Data Fetcher** 是一款面向量化交易者的全维度数据采集与可视化系统。它从零 API Key 出发，通过网页抓取聚合 10+ 个免费数据源，为 SPY、GDXU、SOXX 等标的提供实时行情、技术指标、宏观指标、市场情绪、期权数据、经济日历等一站式数据看板。

### 核心功能

| 功能 | 说明 |
|------|------|
| **实时行情** | Yahoo Finance 实时价格、RSI、ATR、SMA |
| **技术指标** | Finviz 技术指标（RSI、MACD、ADX、OBV 等） |
| **市场情绪** | CNN Fear & Greed 指数、AAII 投资者情绪 |
| **宏观指标** | FRED 经济数据（美债收益率、GDP、CPI、初请失业金等） |
| **期权数据** | 期权链、Put/Call 比率、Max Pain |
| **暗池数据** | 暗池交易量占比、交易所明细 |
| **市场广度** | NYSE 涨跌比、新高新低、板块表现 |
| **经济日历** | 本周重要经济事件与预期 |
| **30 天历史** | 每日 OHLCV 柱状图（Canvas 绘制） |
| **AI 评分** | 多因子加权评分引擎，输出多空信号与百分比 |

### 技术架构

```
quant_data_fetcher/
├── app.py                  # Flask 主程序，REST API + 60s 缓存
├── config.py               # 标的配置与宏观指标列表
├── fetch_all.py            # 全量抓取脚本（CLI 模式）
├── indicator_scorer.py     # AI 评分引擎（13 因子加权）
├── start.bat               # Windows 一键启动
├── fetchers/               # 12 个独立数据抓取模块
│   ├── yahoo_fetcher.py    # Yahoo Finance 行情
│   ├── finviz_fetcher.py   # Finviz 技术指标
│   ├── cnn_sentiment.py    # CNN Fear & Greed
│   ├── fred_fetcher.py     # FRED 宏观数据
│   ├── dark_pool.py        # 暗池数据
│   ├── market_breadth.py   # 市场广度
│   ├── options_fetcher.py  # 期权数据
│   ├── econ_calendar.py    # 经济日历
│   ├── historical_prices.py # 30 天 OHLCV
│   └── ...
├── templates/index.html    # 暗色主题 Dashboard
├── static/
│   ├── style.css           # 暗色主题样式
│   └── app.js              # 前端渲染 + Canvas 图表
└── cache/                  # JSON 缓存目录
```

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourname/quant-data-fetcher.git
cd quant-data-fetcher

# 安装依赖
pip install -r requirements.txt

# 启动（Windows）
start.bat

# 或手动启动
python app.py
```

### 依赖

- Python 3.9+
- Flask 3.x
- requests
- beautifulsoup4
- lxml

### 使用

启动后打开 http://127.0.0.1:5050

- **Dashboard**: 实时数据看板，含行情、指标、情绪、评分
- **Markdown**: 一键导出所有数据为 Markdown 格式
- **API**: `GET /api/data` 返回完整 JSON
- **API**: `GET /api/score` 返回 AI 评分

### 缓存策略

| 数据类型 | 缓存时间 | 说明 |
|----------|----------|------|
| 实时行情 | 60 秒 | TTL 缓存，避免频繁请求 |
| 历史 OHLCV | 永久 | 历史数据不变，仅当天缺失时 fetch |
| 宏观数据 | 60 秒 | FRED 等日频数据 |

### 数据源状态

| 数据源 | 状态 | 备注 |
|--------|------|------|
| Yahoo Finance | 正常 | 行情 + 技术指标 |
| Finviz | 正常 | 技术指标 |
| CNN Fear & Greed | 正常 | 市场情绪 |
| FRED | 正常 | 宏观数据 |
| Dark Pool | 正常 | 暗池占比 |
| Market Breadth | 正常 | 涨跌比 + 板块 |
| Options | 正常 | 期权链 |
| AAII | 受限 | CloudFlare 反爬 |
| CFTC COT | 受限 | URL 变更待修复 |

### 开源协议

MIT License

---

## 日本語

### 概要

**Quant Data Fetcher** は、クオンタトレーダー向けのフルディメンションデータ取得・可視化システムです。API Key 不要で、10 以上の無料データソースをウェブスクレイピングで統合し、SPY・GDXU・SOXX などの銘柄に対してリアルタイム相場、テクニカル指標、マクロ指標、市場心理、オプションデータ、経済カレンダーなどをワンストップで提供します。

### 主な機能

| 機能 | 説明 |
|------|------|
| **リアルタイム相場** | Yahoo Finance リアルタイム価格、RSI、ATR、SMA |
| **テクニカル指標** | Finviz テクニカル指標（RSI、MACD、ADX、OBV など） |
| **市場心理** | CNN Fear & Greed 指数、AAII 投資家心理 |
| **マクロ指標** | FRED 経済データ（米国債利回り、GDP、CPI、新規失業保険申請件数など） |
| **オプションデータ** | オプションチェーン、Put/Call 比率、Max Pain |
| **ダークプール** | ダークプール取引量比率、取引所内訳 |
| **市場広度** | NYSE 騰落率、新高値・新安値、セクター別パフォーマンス |
| **経済カレンダー** | 今週の重要経済イベントと予想値 |
| **30 日履歴** | 日次 OHLCV バーチャート（Canvas 描画） |
| **AI スコア** | 多因子加重スコアリングエンジン、売買シグナルとパーセンテージ出力 |

### 技術構成

```
quant_data_fetcher/
├── app.py                  # Flask メインプログラム、REST API + 60秒キャッシュ
├── config.py               # 銘柄設定とマクロ指標リスト
├── fetch_all.py            # フルスクラップスクリプト（CLI モード）
├── indicator_scorer.py     # AI スコアリングエンジン（13 因子加重）
├── start.bat               # Windows ワンクリック起動
├── fetchers/               # 12 の独立データ取得モジュール
│   ├── yahoo_fetcher.py    # Yahoo Finance 相場
│   ├── finviz_fetcher.py   # Finviz テクニカル指標
│   ├── cnn_sentiment.py    # CNN Fear & Greed
│   ├── fred_fetcher.py     # FRED マクロデータ
│   ├── dark_pool.py        # ダークプールデータ
│   ├── market_breadth.py   # 市場広度
│   ├── options_fetcher.py  # オプションデータ
│   ├── econ_calendar.py    # 経済カレンダー
│   ├── historical_prices.py # 30 日 OHLCV
│   └── ...
├── templates/index.html    # ダークテーマ Dashboard
├── static/
│   ├── style.css           # ダークテーマスタイル
│   └── app.js              # フロントエンドレンダリング + Canvas チャート
└── cache/                  # JSON キャッシュディレクトリ
```

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/yourname/quant-data-fetcher.git
cd quant-data-fetcher

# 依存関係をインストール
pip install -r requirements.txt

# 起動（Windows）
start.bat

# または手動起動
python app.py
```

### 依存関係

- Python 3.9+
- Flask 3.x
- requests
- beautifulsoup4
- lxml

### 使い方

起動後、http://127.0.0.1:5050 を開く

- **Dashboard**: リアルタイムデータダッシュボード（相場、指標、心理、スコア）
- **Markdown**: すべてのデータを Markdown 形式で一括エクスポート
- **API**: `GET /api/data` で完全な JSON を取得
- **API**: `GET /api/score` で AI スコアを取得

### キャッシュ戦略

| データ種別 | キャッシュ時間 | 説明 |
|------------|----------------|------|
| リアルタイム相場 | 60 秒 | TTL キャッシュ、頻繁なリクエストを防止 |
| 履歴 OHLCV | 永久 | 履歴データは不変、当日データが欠損時のみ fetch |
| マクロデータ | 60 秒 | FRED など日次データ |

### データソース状態

| データソース | 状態 | 備考 |
|--------------|------|------|
| Yahoo Finance | 正常 | 相場 + テクニカル指標 |
| Finviz | 正常 | テクニカル指標 |
| CNN Fear & Greed | 正常 | 市場心理 |
| FRED | 正常 | マクロデータ |
| Dark Pool | 正常 | ダークプール比率 |
| Market Breadth | 正常 | 騰落率 + セクター |
| Options | 正常 | オプションチェーン |
| AAII | 制限あり | CloudFlare ボット対策 |
| CFTC COT | 制限あり | URL 変更、修正待ち |

### ライセンス

MIT License

---

## English

### Overview

**Quant Data Fetcher** is a full-dimensional data acquisition and visualization system for quantitative traders. Zero API Key required — it aggregates 10+ free data sources via web scraping to provide a one-stop data dashboard for tickers like SPY, GDXU, and SOXX, covering real-time quotes, technical indicators, macro indicators, market sentiment, options data, economic calendar, and more.

### Key Features

| Feature | Description |
|---------|-------------|
| **Real-time Quotes** | Yahoo Finance real-time prices, RSI, ATR, SMA |
| **Technical Indicators** | Finviz technicals (RSI, MACD, ADX, OBV, etc.) |
| **Market Sentiment** | CNN Fear & Greed Index, AAII Investor Sentiment |
| **Macro Indicators** | FRED economic data (Treasury yields, GDP, CPI, jobless claims, etc.) |
| **Options Data** | Options chain, Put/Call ratio, Max Pain |
| **Dark Pool** | Dark pool volume ratio, exchange breakdown |
| **Market Breadth** | NYSE advance/decline, new highs/lows, sector performance |
| **Economic Calendar** | This week's key economic events and expectations |
| **30-Day History** | Daily OHLCV bar charts (Canvas rendered) |
| **AI Scoring** | Multi-factor weighted scoring engine, bullish/bearish signals with percentages |

### Architecture

```
quant_data_fetcher/
├── app.py                  # Flask main, REST API + 60s cache
├── config.py               # Ticker config & macro series list
├── fetch_all.py            # Full scraper script (CLI mode)
├── indicator_scorer.py     # AI scoring engine (13-factor weighted)
├── start.bat               # Windows one-click start
├── fetchers/               # 12 independent data fetcher modules
│   ├── yahoo_fetcher.py    # Yahoo Finance quotes
│   ├── finviz_fetcher.py   # Finviz technicals
│   ├── cnn_sentiment.py    # CNN Fear & Greed
│   ├── fred_fetcher.py     # FRED macro data
│   ├── dark_pool.py        # Dark pool data
│   ├── market_breadth.py   # Market breadth
│   ├── options_fetcher.py  # Options data
│   ├── econ_calendar.py    # Economic calendar
│   ├── historical_prices.py # 30-day OHLCV
│   └── ...
├── templates/index.html    # Dark theme Dashboard
├── static/
│   ├── style.css           # Dark theme styles
│   └── app.js              # Frontend rendering + Canvas charts
└── cache/                  # JSON cache directory
```

### Installation

```bash
# Clone repo
git clone https://github.com/yourname/quant-data-fetcher.git
cd quant-data-fetcher

# Install dependencies
pip install -r requirements.txt

# Start (Windows)
start.bat

# Or manually
python app.py
```

### Dependencies

- Python 3.9+
- Flask 3.x
- requests
- beautifulsoup4
- lxml

### Usage

After starting, open http://127.0.0.1:5050

- **Dashboard**: Real-time data dashboard with quotes, indicators, sentiment, scores
- **Markdown**: One-click export all data to Markdown format
- **API**: `GET /api/data` returns full JSON
- **API**: `GET /api/score` returns AI scores

### Caching Strategy

| Data Type | Cache Time | Notes |
|-----------|-----------|-------|
| Real-time quotes | 60s | TTL cache, prevents excessive requests |
| Historical OHLCV | Permanent | Historical data never changes, only fetch when today's bar is missing |
| Macro data | 60s | Daily-frequency data from FRED etc. |

### Data Source Status

| Source | Status | Notes |
|--------|--------|-------|
| Yahoo Finance | OK | Quotes + technicals |
| Finviz | OK | Technical indicators |
| CNN Fear & Greed | OK | Market sentiment |
| FRED | OK | Macro data |
| Dark Pool | OK | Dark pool ratio |
| Market Breadth | OK | Advance/decline + sectors |
| Options | OK | Options chain |
| AAII | Limited | CloudFlare bot protection |
| CFTC COT | Limited | URL changed, pending fix |

### License

MIT License
