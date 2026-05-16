# AI-Quant — 智能量化决策引擎

> AI自动量化交易程序 / AI自動クオンタトレードシステム / AI-Powered Quantitative Trading Engine

---

## 中文

### 🚀 项目简介

**AI-Quant** 是一款基于人工智能的多因子量化决策引擎。它通过自研的分布式数据采集网络，实时聚合全球 10+ 权威金融数据源，运用 13 维加权评分算法对市场进行深度量化分析，为交易者提供机构级的多空信号与风险评估。

这不是一个普通的"数据抓取工具"——它是一个具备**智能分析能力**的量化决策系统。

### 🧠 AI 核心能力

| 能力层级 | 功能 | 技术实现 |
|----------|------|----------|
| **感知层** | 多源异构数据采集 | 12 个独立 Fetcher 模块，零 API Key 覆盖全球数据 |
| **认知层** | 13 因子量化评分 | 技术指标 × 情绪指标 × 宏观指标 × 期权指标 加权融合 |
| **决策层** | 多空信号输出 | STRONGLY_BULLISH → STRONGLY_BEARISH 七级信号 + 百分比分解 |
| **可视化层** | 实时 Canvas 渲染 | 暗色主题 Dashboard，OHLCV 柱状图、评分热力图 |

### 📊 13 维 AI 评分因子

1. **RSI 超买超卖** — 动量反转信号
2. **MACD 趋势强度** — 多空动能对比
3. **ADX 趋势方向** — 趋势确认度
4. **OBV 量价背离** — 资金流入流出
5. **Fear & Greed 情绪** — 市场极端情绪捕捉
6. **VIX 恐慌指数** — 波动率预期
7. **美债收益率曲线** — 宏观经济前瞻
8. **Put/Call 比率** — 期权市场押注方向
9. **暗池资金流向** — 机构大宗交易意图
10. **市场广度** — NYSE 涨跌比、新高新低
11. **经济日历事件** — 宏观事件冲击预警
12. **历史波动率** — 30 日价格分布特征
13. **跨资产相关性** — 股债金三角联动

### 🏗️ 系统架构

```
AI-Quant/
├── 🧠 brain/                    # AI 决策核心
│   ├── indicator_scorer.py      # 13 因子加权评分引擎
│   └── scoring_models/          # 可插拔评分模型
├── 📡 sensors/                  # 分布式数据采集
│   ├── yahoo_fetcher.py         # Yahoo Finance 实时行情
│   ├── finviz_fetcher.py        # Finviz 技术指标矩阵
│   ├── cnn_sentiment.py         # CNN Fear & Greed 情绪指数
│   ├── fred_fetcher.py          # FRED 美联储宏观数据库
│   ├── dark_pool.py             # 暗池资金流向追踪
│   ├── market_breadth.py        # NYSE 市场广度监测
│   ├── options_fetcher.py       # 期权链 + Max Pain 分析
│   ├── econ_calendar.py         # 经济日历事件预警
│   ├── historical_prices.py     # 30 日 OHLCV 历史回溯
│   └── ...
├── 🖥️ cockpit/                  # 指挥舱（前端）
│   ├── templates/index.html     # 暗色主题 Dashboard
│   └── static/
│       ├── style.css            # 赛博朋克暗色 UI
│       └── app.js               # Canvas 实时渲染引擎
├── ⚡ core/                     # 系统核心
│   ├── app.py                   # Flask 异步 API 网关
│   ├── config.py                # 标的配置 + 宏观指标矩阵
│   └── fetch_all.py             # 批量数据采集 CLI
├── 💾 memory/                   # 智能缓存层
│   └── cache/                   # 分层缓存（实时 60s / 历史永久）
└── 🚀 start.bat                 # 一键启动
```

### 🎯 核心功能

| 功能模块 | 说明 | AI 级别 |
|----------|------|---------|
| **实时行情矩阵** | Yahoo Finance 实时价格 + RSI/ATR/SMA 技术矩阵 | L1 感知 |
| **技术指标融合** | Finviz 多维度技术信号聚合 | L2 认知 |
| **情绪量化引擎** | CNN Fear & Greed + AAII 投资者情绪双因子 | L2 认知 |
| **宏观前瞻雷达** | FRED 美债/GDP/CPI/就业 四维宏观扫描 | L2 认知 |
| **期权博弈分析** | Put/Call 比率 + Max Pain 机构意图解码 | L3 决策 |
| **暗池资金追踪** | 17 交易所暗池占比，机构大宗交易透视 | L3 决策 |
| **市场广度监测** | NYSE 涨跌比 + 新高新低 + 11 板块热力图 | L2 认知 |
| **经济事件预警** | 本周宏观事件时间表 + 预期冲击评估 | L2 认知 |
| **历史回溯分析** | 30 日 OHLCV Canvas 柱状图，波动特征识别 | L2 认知 |
| **AI 综合评分** | 13 因子加权融合，七级多空信号 + 百分比分解 | L3 决策 |

### ⚡ 技术亮点

- **零 API Key 架构**：纯网页智能解析，无需任何付费 API
- **分布式 Fetcher**：12 个独立模块，单点故障不影响全局
- **智能缓存策略**：实时数据 60s TTL，历史数据永久缓存，跨天零请求
- **Canvas 实时渲染**：前端零依赖，60fps 流畅图表
- **Markdown 一键导出**：完整量化分析报告生成
- **RESTful API**：`/api/data` 全量数据，`/api/score` AI 评分

### 🛠️ 快速开始

```bash
# 克隆仓库
git clone https://github.com/moiraroman/ai-quant.git
cd ai-quant

# 安装依赖
pip install -r requirements.txt

# 一键启动
start.bat

# 打开 Dashboard
# http://127.0.0.1:5050
```

### 📡 数据源网络

| 数据源 | 类型 | 状态 | 覆盖维度 |
|--------|------|------|----------|
| Yahoo Finance | 实时行情 | ✅ 正常 | 价格、RSI、ATR、SMA |
| Finviz | 技术指标 | ✅ 正常 | RSI、MACD、ADX、OBV |
| CNN Fear & Greed | 市场情绪 | ✅ 正常 | 恐惧贪婪指数 |
| FRED (美联储) | 宏观数据 | ✅ 正常 | 美债、GDP、CPI、就业 |
| Dark Pool (ChartExchange) | 机构资金 | ✅ 正常 | 暗池占比、交易所明细 |
| MarketWatch | 行情验证 | ✅ 正常 | 交叉验证价格 |
| Options (Yahoo) | 期权数据 | ✅ 正常 | 期权链、Put/Call |
| Econ Calendar | 事件预警 | ✅ 正常 | 宏观事件时间表 |
| AAII | 投资者情绪 | ⚠️ 受限 | CloudFlare 防护 |
| CFTC COT | 期货持仓 | ⚠️ 受限 | URL 变更中 |

### 📜 开源协议

MIT License — 自由使用，欢迎贡献

---

## 日本語

### 🚀 プロジェクト概要

**AI-Quant** は、人工知能を基盤とした多因子クオンタ意思決定エンジンです。自社開発の分散型データ取得ネットワークを通じて、世界 10 以上の権威ある金融データソースをリアルタイムに集約し、13 次元の加重スコアリングアルゴリズムで市場を深く定量分析し、トレーダーに機関レベルの売買シグナルとリスク評価を提供します。

これは単なる「データ取得ツール」ではありません——**知的分析能力**を持つクオンタ意思決定システムです。

### 🧠 AI コア機能

| 能力レイヤー | 機能 | 技術実装 |
|--------------|------|----------|
| **知覚層** | 多源異種データ収集 | 12 の独立 Fetcher モジュール、API Key 不要で世界データをカバー |
| **認知層** | 13 因子定量スコア | 技術指標 × 心理指標 × マクロ指標 × オプション指標 の加重融合 |
| **意思決定層** | 売買シグナル出力 | STRONGLY_BULLISH → STRONGLY_BEARISH 7 段階シグナル + パーセンテージ分解 |
| **可視化層** | リアルタイム Canvas 描画 | ダークテーマ Dashboard、OHLCV バーチャート、スコアヒートマップ |

### 📊 13 次元 AI スコアリング因子

1. **RSI 買われすぎ・売られすぎ** — モメンタム反転シグナル
2. **MACD トレンド強度** — 売買勢力対比
3. **ADX トレンド方向** — トレンド確認度
4. **OBV 価格・出来高乖離** — 資金流入流出
5. **Fear & Greed 心理** — 市場極端心理捕捉
6. **VIX 恐怖指数** — ボラティリティ予期
7. **米国債利回り曲線** — マクロ経済先行指標
8. **Put/Call 比率** — オプション市場の賭け方向
9. **ダークプール資金流** — 機関大口取引意図
10. **市場広度** — NYSE 騰落率、新高値・新安値
11. **経済カレンダー** — マクロイベント衝撃警報
12. **履歴ボラティリティ** — 30 日価格分布特性
13. **クロスアセット相関** — 株・債・金トライアングル連動

### 🏗️ システムアーキテクチャ

```
AI-Quant/
├── 🧠 brain/                    # AI 意思決定コア
│   ├── indicator_scorer.py      # 13 因子加重スコアリングエンジン
│   └── scoring_models/          # プラガブルスコアリングモデル
├── 📡 sensors/                  # 分散型データ取得
│   ├── yahoo_fetcher.py         # Yahoo Finance リアルタイム相場
│   ├── finviz_fetcher.py        # Finviz 技術指標マトリックス
│   ├── cnn_sentiment.py         # CNN Fear & Greed 心理指数
│   ├── fred_fetcher.py          # FRED マクロデータベース
│   ├── dark_pool.py             # ダークプール資金流追跡
│   ├── market_breadth.py        # NYSE 市場広度監視
│   ├── options_fetcher.py       # オプションチェーン + Max Pain 分析
│   ├── econ_calendar.py         # 経済カレンダーイベント警報
│   ├── historical_prices.py     # 30 日 OHLCV 履歴回溯
│   └── ...
├── 🖥️ cockpit/                  # コックピット（フロントエンド）
│   ├── templates/index.html     # ダークテーマ Dashboard
│   └── static/
│       ├── style.css            # サイバーパンク暗色 UI
│       └── app.js               # Canvas リアルタイムレンダリングエンジン
├── ⚡ core/                     # システムコア
│   ├── app.py                   # Flask 非同期 API ゲートウェイ
│   ├── config.py                # 銘柄設定 + マクロ指標マトリックス
│   └── fetch_all.py             # バッチデータ取得 CLI
├── 💾 memory/                   # インテリジェントキャッシュ層
│   └── cache/                   # 階層キャッシュ（リアルタイム 60s / 履歴永久）
└── 🚀 start.bat                 # ワンクリック起動
```

### 🎯 主な機能

| 機能モジュール | 説明 | AI レベル |
|----------------|------|-----------|
| **リアルタイム相場マトリックス** | Yahoo Finance リアルタイム価格 + RSI/ATR/SMA 技術マトリックス | L1 知覚 |
| **技術指標融合** | Finviz 多次元技術シグナル集約 | L2 認知 |
| **心理定量化エンジン** | CNN Fear & Greed + AAII 投資家心理双因子 | L2 認知 |
| **マクロ先行レーダー** | FRED 米国債/GDP/CPI/雇用 4 次元マクロスキャン | L2 認知 |
| **オプション博弈分析** | Put/Call 比率 + Max Pain 機関意図デコード | L3 意思決定 |
| **ダークプール資金追跡** | 17 取引所ダークプール比率、機関大口取引透視 | L3 意思決定 |
| **市場広度監視** | NYSE 騰落率 + 新高値・新安値 + 11 セクターヒートマップ | L2 認知 |
| **経済イベント警報** | 今週マクロイベント時刻表 + 予期衝撃評価 | L2 認知 |
| **履歴回溯分析** | 30 日 OHLCV Canvas バーチャート、ボラティリティ特性識別 | L2 認知 |
| **AI 総合スコア** | 13 因子加重融合、7 段階売買シグナル + パーセンテージ分解 | L3 意思決定 |

### ⚡ 技術ハイライト

- **ゼロ API Key アーキテクチャ**：純粋ウェブ知能解析、有料 API 不要
- **分散型 Fetcher**：12 の独立モジュール、単一点故障が全体に影響しない
- **インテリジェントキャッシュ戦略**：リアルタイムデータ 60s TTL、履歴データ永久キャッシュ、日をまたいでゼロリクエスト
- **Canvas リアルタイム描画**：フロントエンドゼロ依存、60fps 滑らかチャート
- **Markdown ワンクリックエクスポート**：完全な定量分析レポート生成
- **RESTful API**：`/api/data` 全量データ、`/api/score` AI スコア

### 🛠️ クイックスタート

```bash
# リポジトリをクローン
git clone https://github.com/moiraroman/ai-quant.git
cd ai-quant

# 依存関係をインストール
pip install -r requirements.txt

# ワンクリック起動
start.bat

# Dashboard を開く
# http://127.0.0.1:5050
```

### 📡 データソースネットワーク

| データソース | タイプ | 状態 | カバー次元 |
|--------------|--------|------|------------|
| Yahoo Finance | リアルタイム相場 | ✅ 正常 | 価格、RSI、ATR、SMA |
| Finviz | 技術指標 | ✅ 正常 | RSI、MACD、ADX、OBV |
| CNN Fear & Greed | 市場心理 | ✅ 正常 | 恐怖・強欲指数 |
| FRED (FRB) | マクロデータ | ✅ 正常 | 米国債、GDP、CPI、雇用 |
| Dark Pool (ChartExchange) | 機関資金 | ✅ 正常 | ダークプール比率、取引所内訳 |
| MarketWatch | 相場検証 | ✅ 正常 | クロス検証価格 |
| Options (Yahoo) | オプションデータ | ✅ 正常 | オプションチェーン、Put/Call |
| Econ Calendar | イベント警報 | ✅ 正常 | マクロイベント時刻表 |
| AAII | 投資家心理 | ⚠️ 制限あり | CloudFlare 保護 |
| CFTC COT | 先物持高 | ⚠️ 制限あり | URL 変更中 |

### 📜 ライセンス

MIT License — 自由に使用、貢献歓迎

---

## English

### 🚀 Project Overview

**AI-Quant** is an AI-powered multi-factor quantitative decision engine. Through a self-developed distributed data acquisition network, it aggregates 10+ authoritative global financial data sources in real-time, applies a 13-dimensional weighted scoring algorithm for deep quantitative market analysis, and provides traders with institutional-grade bullish/bearish signals and risk assessments.

This is not an ordinary "data scraper" — it is a quantitative decision system with **intelligent analytical capabilities**.

### 🧠 AI Core Capabilities

| Capability Layer | Function | Technical Implementation |
|------------------|----------|--------------------------|
| **Perception** | Multi-source heterogeneous data acquisition | 12 independent Fetcher modules, zero API Key global coverage |
| **Cognition** | 13-factor quantitative scoring | Technical × Sentiment × Macro × Options weighted fusion |
| **Decision** | Bullish/bearish signal output | STRONGLY_BULLISH → STRONGLY_BEARISH 7-level signals + percentage breakdown |
| **Visualization** | Real-time Canvas rendering | Dark theme Dashboard, OHLCV bar charts, score heatmaps |

### 📊 13-Dimensional AI Scoring Factors

1. **RSI Overbought/Oversold** — Momentum reversal signals
2. **MACD Trend Strength** — Bull/bear momentum comparison
3. **ADX Trend Direction** — Trend confirmation degree
4. **OBV Price-Volume Divergence** — Capital inflow/outflow
5. **Fear & Greed Sentiment** — Market extreme sentiment capture
6. **VIX Fear Index** — Volatility expectations
7. **Treasury Yield Curve** — Macroeconomic forward indicators
8. **Put/Call Ratio** — Options market directional bets
9. **Dark Pool Capital Flow** — Institutional block trade intent
10. **Market Breadth** — NYSE advance/decline, new highs/lows
11. **Economic Calendar Events** — Macro event impact warnings
12. **Historical Volatility** — 30-day price distribution characteristics
13. **Cross-Asset Correlation** — Equity-bond-gold triangle linkage

### 🏗️ System Architecture

```
AI-Quant/
├── 🧠 brain/                    # AI Decision Core
│   ├── indicator_scorer.py      # 13-factor weighted scoring engine
│   └── scoring_models/          # Pluggable scoring models
├── 📡 sensors/                  # Distributed Data Acquisition
│   ├── yahoo_fetcher.py         # Yahoo Finance real-time quotes
│   ├── finviz_fetcher.py        # Finviz technical indicator matrix
│   ├── cnn_sentiment.py         # CNN Fear & Greed sentiment index
│   ├── fred_fetcher.py          # FRED Federal Reserve macro database
│   ├── dark_pool.py             # Dark pool capital flow tracking
│   ├── market_breadth.py        # NYSE market breadth monitoring
│   ├── options_fetcher.py       # Options chain + Max Pain analysis
│   ├── econ_calendar.py         # Economic calendar event alerts
│   ├── historical_prices.py     # 30-day OHLCV historical backtest
│   └── ...
├── 🖥️ cockpit/                  # Cockpit (Frontend)
│   ├── templates/index.html     # Dark theme Dashboard
│   └── static/
│       ├── style.css            # Cyberpunk dark UI
│       └── app.js               # Canvas real-time rendering engine
├── ⚡ core/                     # System Core
│   ├── app.py                   # Flask async API gateway
│   ├── config.py                # Ticker config + macro indicator matrix
│   └── fetch_all.py             # Batch data acquisition CLI
├── 💾 memory/                   # Intelligent Cache Layer
│   └── cache/                   # Tiered cache (real-time 60s / historical permanent)
└── 🚀 start.bat                 # One-click start
```

### 🎯 Core Features

| Feature Module | Description | AI Level |
|----------------|-------------|----------|
| **Real-time Quote Matrix** | Yahoo Finance real-time prices + RSI/ATR/SMA technical matrix | L1 Perception |
| **Technical Indicator Fusion** | Finviz multi-dimensional technical signal aggregation | L2 Cognition |
| **Sentiment Quantification Engine** | CNN Fear & Greed + AAII investor sentiment dual-factor | L2 Cognition |
| **Macro Forward Radar** | FRED Treasury/GDP/CPI/employment 4D macro scan | L2 Cognition |
| **Options Game Theory Analysis** | Put/Call ratio + Max Pain institutional intent decoding | L3 Decision |
| **Dark Pool Capital Tracking** | 17-exchange dark pool ratio, institutional block trade insight | L3 Decision |
| **Market Breadth Monitoring** | NYSE advance/decline + new highs/lows + 11-sector heatmap | L2 Cognition |
| **Economic Event Warnings** | This week's macro event schedule + expected impact assessment | L2 Cognition |
| **Historical Backtest Analysis** | 30-day OHLCV Canvas bar charts, volatility pattern recognition | L2 Cognition |
| **AI Composite Score** | 13-factor weighted fusion, 7-level signal + percentage breakdown | L3 Decision |

### ⚡ Technical Highlights

- **Zero API Key Architecture**: Pure web intelligent parsing, no paid APIs required
- **Distributed Fetchers**: 12 independent modules, single-point failure doesn't affect global operation
- **Intelligent Caching**: Real-time 60s TTL, historical permanent cache, zero requests across days
- **Canvas Real-time Rendering**: Zero frontend dependencies, 60fps smooth charts
- **Markdown One-click Export**: Complete quantitative analysis report generation
- **RESTful API**: `/api/data` full data, `/api/score` AI scores

### 🛠️ Quick Start

```bash
# Clone repo
git clone https://github.com/moiraroman/ai-quant.git
cd ai-quant

# Install dependencies
pip install -r requirements.txt

# One-click start
start.bat

# Open Dashboard
# http://127.0.0.1:5050
```

### 📡 Data Source Network

| Data Source | Type | Status | Coverage |
|-------------|------|--------|----------|
| Yahoo Finance | Real-time quotes | ✅ OK | Price, RSI, ATR, SMA |
| Finviz | Technical indicators | ✅ OK | RSI, MACD, ADX, OBV |
| CNN Fear & Greed | Market sentiment | ✅ OK | Fear-greed index |
| FRED (Federal Reserve) | Macro data | ✅ OK | Treasury, GDP, CPI, jobs |
| Dark Pool (ChartExchange) | Institutional capital | ✅ OK | Dark pool ratio, exchange breakdown |
| MarketWatch | Quote verification | ✅ OK | Cross-verification price |
| Options (Yahoo) | Options data | ✅ OK | Options chain, Put/Call |
| Econ Calendar | Event alerts | ✅ OK | Macro event schedule |
| AAII | Investor sentiment | ⚠️ Limited | CloudFlare protection |
| CFTC COT | Futures positions | ⚠️ Limited | URL changed |

### 📜 License

MIT License — Free to use, contributions welcome
