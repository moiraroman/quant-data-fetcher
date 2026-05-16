# 提示词数据源全覆盖分析 & 一键抓取系统

## 一、数据源分析

基于提示词要求，逐项分析所有需要从网站获取的数据：

### ✅ 可获取（已实现）

| # | 数据 | 数据源 | 方式 | 状态 |
|---|------|--------|------|------|
| 1 | 美东日期+时间 | time.is | HTML parse (BS4) | ✅ |
| 2 | 交易时段判断 | time.is 解析结果 | 小时数 → REGULAR/PRE/POST/CLOSED | ✅ |
| 3 | SPY/GDXU/SOXX 实时价格 | Yahoo Finance v7 Quote | Cookie/Crumb + JSON API | ✅ |
| 4 | VIX/DXY/US10Y/GOLD 实时 | Yahoo Finance (^VIX, DX-Y.NYB, ^TNX, GC=F) | v7 Quote API | ✅ |
| 5 | HYG/JNK 信用债价格 | Yahoo Finance (HYG, JNK) | v7 Quote API | ✅ |
| 6 | MA50/MA200 精确值 | Yahoo Finance | v7 Quote (fiftyDayAverage/twoHundredDayAverage) | ✅ |
| 7 | RSI(14)/ATR(14) | Finviz | HTML scrape (BS4) | ✅ |
| 8 | SMA20/50/200% | Finviz | HTML scrape (BS4) | ✅ |
| 9 | 周/月/季/半年/YTD/年收益 | Finviz | HTML scrape (BS4) | ✅ |
| 10 | Beta/RelVol | Finviz | HTML scrape (BS4) | ✅ |
| 11 | CNN Fear & Greed 指数 | CNN JSON API | GET + browser headers (防418) | ✅ |
| 12 | FRED VIX (T-1 收盘) | FRED graph CSV | ?id=VIXCLS | ✅ |
| 13 | 10Y TIPS 实际收益率 | FRED graph CSV | ?id=DFII10 | ✅ |
| 14 | 美股经济日历 (未来5日) | 固定日程推算 + MW/Econoday scrape | 每周四初请 + 月频CPI/NFP推算 | ✅ |
| 15 | MarketWatch 价格(双源验证) | MarketWatch | HTML scrape (不同ticker成功率不同) | 🟡 部分成功 |

### ❌ 不可获取（JS渲染/付费墙/会员制）

| # | 数据 | 尝试的来源 | 失败原因 |
|---|------|-----------|---------|
| 1 | GEX (Gamma Exposure) | SpotGamma, Barchart | 付费数据/JS渲染 |
| 2 | Max Pain | OptionCharts.io, Barchart | JS渲染 |
| 3 | VPVR/Volume Profile | TradingView | JS动态渲染 |
| 4 | VIX Term Structure | CBOE, Barchart | JS渲染 |
| 5 | Put/Call Ratio (精确日值) | CBOE, Barchart | JS渲染 |
| 6 | NH/NL Ratio | NYSE | JS渲染 |
| 7 | Advance/Decline Ratio | NYSE | JS渲染 |
| 8 | ETF Fund Flows (精确) | ETF.com, FactSet, SSGA | 付费/JS渲染 |
| 9 | AAII Sentiment | AAII | 会员制 |
| 10 | CTA Positioning | 专业数据终端 | 付费专属 |
| 11 | SPY vs RSP 收益分化 | ETF.com | JS渲染 |
| 12 | XLK vs XLU 板块轮动 | TradingView | JS渲染 |
| 13 | TradingView 技术指标页 | TradingView | JS渲染 |
| 14 | Investing.com 图表 | Investing.com | JS渲染 |
| 15 | Google Finance | Google | JS渲染 |
| 16 | Seeking Alpha | Seeking Alpha | 付费/JS渲染 |
| 17 | State Street SPY 报表 | SSGA | PDF/付费API |
| 18 | ForexFactory 日历 | ForexFactory | JS渲染 |

## 二、一键抓取 — fetch_all.py

```bash
cd quant_data_fetcher
pip install -r requirements.txt
python fetch_all.py                    # JSON stdout
python fetch_all.py --summary-only     # 终端摘要
python fetch_all.py -o data.json       # 保存文件
```

## 三、实测输出摘要

```
==============================================================================
  Quant Data Fetcher — 全量数据抓取报告
==============================================================================

  [TIME] 美东时间: 2026年5月5日周二 20:48 EDT (已收盘)
  [DUR] : 17.2s

  [QUOTES] 行情快照
  SPY    $   723.77  ▲ +0.80%  |  Vol: 31.84M
  GDXU   $   156.93  ▲ +1.70%  |  Vol: 470K
  SOXX   $   484.61  ▲ +4.88%  |  Vol: --

  [TECH] 技术指标 (Finviz)
  指标           SPY      GDXU      SOXX
  RSI(14)      71.10     37.04     77.95
  ATR(14)       7.60     16.53     13.46
  SMA20%        2.20      2.03     12.44
  SMA50%        5.78     -1.09     16.99
  SMA200%       7.29    -43.81     56.87
  周涨跌        1.66      2.09      3.41
  月涨跌        9.80     -0.22     42.12
  YTD           6.10    -66.54     49.77
  年涨跌       28.39    -65.36    157.10

  [MACRO] 宏观 & 信用
  VIX          17.41  ▼ -4.81%
  DXY          98.43  ▲ +0.05%
  US10Y         4.41  ▼ -0.72%
  GOLD      4,569.90  ▲ +0.81%
  HYG          79.92  ▲ +0.15%
  JNK          97.52  ▲ +0.12%

  [SENT] 市场情绪
  CNN Fear & Greed: 67.14  (greed)

  [FRED] FRED 经济数据
  VIX           18.29  (2026-05-04)
  TIPS           1.95  (2026-05-04)

  [CAL] 经济日历 (未来5交易日)
  2026-05-11~2026-05-14   8:30 AM  [EVENT RISK] CPI (MoM) + Core CPI  high
  2026-05-07   8:30 AM  Initial Jobless Claims  medium

  [COMPLETENESS] 数据完整度评估
  可获取数据: 9/11 (82%)
  XX 不可获取: 16项 (全部为JS渲染/付费墙，已逐项确认)
```
