# Quant Mobile Dashboard — Unity WebGL 产品设计文档 v2.0

> **产品定位**: 将 Quant Data Fetcher Web Dashboard 迁移到手机 9:16 竖屏 Unity WebGL 应用
> **数据层**: 复用现有 Flask API (app.py, port 5050)，Unity 通过 UnityWebRequest 消费
> **设计哲学**: 数据与表现完全解耦，Unity 只负责 UI 渲染，Flask 负责数据供应

---

## 1. 产品概述

| 项 | 值 |
|----|-----|
| **产品名称** | Quant Mobile Dashboard |
| **版本** | 1.0 |
| **核心价值** | 手机端美股量化数据仪表盘，竖屏单手操作 |
| **目标用户** | 个人量化交易者，手机随时查看行情 |
| **运行环境** | Unity 6 WebGL → 现代浏览器 (Chrome/Safari) |
| **屏幕规格** | 9:16 竖屏，1080×1920 参考分辨率，自适应缩放 |
| **技术栈** | Unity 6 + C# + UnityWebRequest + TextMeshPro + Newtonsoft.Json |
| **国际化** | 中日英三语实时切换，L10n 翻译表驱动，零硬编码文本 |
| **Skill** | quant-mobile-deploy — 一键场景部署 |

### 与 WebUI 的关系

```
现有 WebUI (Desktop 1400px)        →    Unity Mobile (750×1334, 9:16)
━━━━━━━━━━━━━━━━━━━━━━            ━━━━━━━━━━━━━━━━━━━━━━━━━━
两栏 50/50 布局                    →   全宽单栏，垂直滚动
120px 高卡片                       →   紧凑卡片，信息密度优化
Canvas OHLC 大图 (460×200)        →   迷你 OHLC 图 (全宽×120)
Sector grid (320px 多列)          →   垂直列表
桌面 hover 效果                     →   触控反馈
Tab navigation 顶部                →   底部 Tab Bar
Auto-refresh 60s                   →   自动刷新 + 下拉手动刷新
```

### 新增：国际化 (i18n)

- `L10n.cs` 静态类管理全部翻译，~50 个 key 覆盖所有 UI 文案
- 三语支持：中文 (ZH) / 日本語 (JA) / English (EN)
- 语言切换：StatusBar 内的 LanguageSelectorUI 按钮，点击轮换
- 零硬编码：所有组件用 `L10n.T("key")` 获取文本，订阅 `OnLanguageChanged` 实时刷新
- API 信号词 (STRONGLY_BULLISH 等) 也纳入翻译对照

翻译 Key 分类：Common(通用) / StatusBar / TickerCard / ScoreCard / TechnicalTable / Sentiment / DarkPool / COT / Breadth / Sector / TabBar / Error / Chart / Language

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Unity WebGL 应用                       │
│                                                         │
│  ┌──────────┐   ┌──────────────┐   ┌────────────────┐  │
│  │DataManager│──>│ UIController │──>│ Component UIs  │  │
│  │ HTTP Client│   │ 数据分发      │   │ TickerCard ×3  │  │
│  │ JSON Parse │   │ 缓存管理      │   │ ScoreCard  ×3  │  │
│  │ 60s Timer  │   │ 状态控制      │   │ OHLCChart  ×3  │  │
│  └─────┬─────┘   └──────────────┘   │ TechTable      │  │
│        │                             │ MacroGrid      │  │
│   UnityWebRequest                    │ SentimentPanel │  │
│        │                             │ DarkPoolCards  │  │
│        ▼                             │ COTTable       │  │
│  ┌──────────────────┐                │ BreadthPanel   │  │
│  │  Flask API       │                │ SectorList     │  │
│  │  GET /api/data   │                │ ErrorPanel     │  │
│  │  JSON Response   │                └────────────────┘  │
│  └──────────────────┘                                    │
└─────────────────────────────────────────────────────────┘
```

### 数据流

```
1. DataManager.Start() → 发送 UnityWebRequest GET /api/data
2. 收到 JSON → 反序列化为 MarketData C# 对象
3. UIController.OnDataReceived(data) → 遍历子组件更新
4. 每 60s 自动重新请求，触发增量更新
5. 错误时显示重试按钮，不影响已展示数据
```

---

## 3. UI 布局（9:16 竖屏）

### 3.1 整体结构

```
┌────────────────────────┐  Top Safe Area
│  StatusBar (44px)      │  Logo · 时间 · 刷新按钮 · 状态灯
├────────────────────────┤
│                        │
│  ┌─ Ticker Cards ────┐ │  SPY / GDXU / SOXX (3张全宽卡片)
│  │  SPY  $xxx.xx     │ │  价格 + 涨跌 + RSI Badge + AI评分条
│  ├────────────────────┤ │
│  │  GDXU $xxx.xx     │ │
│  ├────────────────────┤ │
│  │  SOXX $xxx.xx     │ │
│  └────────────────────┘ │
│                        │
│  ┌─ AI Scores ───────┐ │  牛熊评分卡片 (3张)
│  └────────────────────┘ │
│                        │
│  ┌─ 30-Day OHLC ─────┐ │  迷你K线图 (3张 Canvas绘制)
│  └────────────────────┘ │
│                        │
│  ┌─ Technical Table ─┐ │  技术指标表 (横向滚动)
│  │ RSI | SPY | GDXU  │ │
│  └────────────────────┘ │
│                        │
│  ┌─ Macro Grid ──────┐ │  宏观指标 2列网格
│  │ VIX  │  DXY       │ │
│  │ US10Y│  GOLD      │ │
│  │ HYG  │  JNK       │ │
│  └────────────────────┘ │
│                        │
│  ┌─ Sentiment ───────┐ │  情绪面板 CNN + AAII
│  └────────────────────┘ │
│                        │
│  ┌─ Dark Pool ───────┐ │  暗池数据 (3张卡片)
│  └────────────────────┘ │
│                        │
│  ┌─ CFTC COT ────────┐ │  机构持仓表
│  └────────────────────┘ │
│                        │
│  ┌─ Market Breadth ──┐ │  市场宽度
│  └────────────────────┘ │
│                        │
│  ┌─ Sector Perf ─────┐ │  板块表现排名
│  └────────────────────┘ │
│                        │
│  ┌─ Error Log ───────┐ │  错误日志 (可折叠)
│  └────────────────────┘ │
│                        │
├────────────────────────┤
│  TabBar (56px)         │  Dashboard | Raw Data
└────────────────────────┘  Bottom Safe Area
```

### 3.2 配色方案（继承 WebUI Dark Theme）

| Role | Hex | Usage |
|------|-----|-------|
| Background Primary | `#0a0e17` | 页面背景 |
| Background Secondary | `#131a2b` | 区块卡片 |
| Card Background | `#182033` | 内层卡片 |
| Border | `#1e2d47` | 分割线 |
| Text Primary | `#e2e8f0` | 正文 |
| Text Secondary | `#94a3b8` | 标签 |
| Text Muted | `#64748b` | 次要信息 |
| Accent Green | `#00d4aa` | 上涨/看多 |
| Accent Red | `#ff4757` | 下跌/看空 |
| Accent Blue | `#5b9bd5` | 中性/链接 |

### 3.3 间距规范

```
外边距: 12px (所有卡片区块间)
内边距: 14px (卡片内部)
圆角: 8px (卡片), 12px (区块 Section)
字体: TMP_Text, 默认 LiberationSans SDF
```

---

## 4. 组件规格

### 4.1 StatusBar (顶栏)

- 高度: 44px
- Logo "Quant Data Fetcher" + 版本号 Badge
- 时间戳 (UTC)
- 状态灯 (绿=OK, 红=Error)
- 刷新按钮
- 倒计时 (60s)

### 4.2 TickerCard (行情卡片)

- 全宽 - 24px margin
- 高度自适应 (~140px)
- 内容:
  - 右上角 RSI Badge (红≥70, 绿≤30, 蓝中性)
  - Symbol + Name
  - 价格大字 + 涨跌幅
  - 元数据行: Volume, Day High, Day Low
  - AI评分条 (Bull% 绿条 / Bear% 红条) + 信号文本
- 状态: Normal / Loading / Error

### 4.3 ScoreCard (AI评分卡片)

- 全宽 - 24px margin
- Symbol + 信号 Badge (大号, 颜色编码)
- 牛熊比例条 (视觉条形)
- 数字: Bull% / Bear% / Weighted Score
- 颜色映射:
  - STRONGLY_BULLISH: #00d4aa
  - BULLISH: #00d4aa (60% opacity)
  - NEUTRAL: #5b9bd5
  - BEARISH: #ff4757 (60% opacity)
  - STRONGLY_BEARISH: #ff4757

### 4.4 OHLCChart (K线迷你图)

- Canvas (RawImage + Texture2D)
- 尺寸: 全宽×160px
- 手绘 OHLC 柱 (高点→低点 竖线, 开盘→收盘 横线)
- 涨绿跌红
- X轴无刻度，Y轴网格线 + 价格标签
- 30天变化标注

### 4.5 TechnicalTable (技术指标表)

- 横向可滚动 (ScrollRect horizontal)
- 固定第一列 Indicator 名称
- 列: Indicator | SPY | GDXU | SOXX
- 行: RSI(14), ATR(14), SMA20%, SMA50%, SMA200%, Perf W/M/YTD/1Y
- 超买(红)/超卖(绿)/正常(蓝) 颜色编码

### 4.6 MacroGrid (宏观指标)

- 2列网格 (每格 ~170px 宽)
- 6项: VIX, DXY, US10Y, GOLD, HYG, JNK
- 每个: Label + Value大号 + Change%
- FRED对比值标注 (小字)

### 4.7 SentimentPanel (市场情绪)

- CNN Fear & Greed: Score + Rating (颜色编码恐惧/贪婪)
- AAII: Bullish% / Neutral% / Bearish% / Spread
- AAII日期标注

### 4.8 DarkPoolCard (暗池)
- 3张卡片 (SPY/GDXU/SOXX)
- Dark Pool% (红色) / Lit% (蓝色)
- DP Volume / 30d Avg DP%
- Signal Badge (BULLISH/BEARISH/NEUTRAL)

### 4.9 COTTable (机构持仓)
- 表格: Commodity | Date | AM Net | LF Net | DL Net | Total OI
- 正绿负红色

### 4.10 BreadthPanel (市场宽度)
- 大号 Signal Badge
- Advance Ratio + Adv/Dec 数据
- NYSE Index (如有)

### 4.11 SectorPanel (板块)
- 垂直列表，按 Change% 降序
- 每行: Symbol | Name | 条形图 | Change%
- 条形: 绿色正/红色负，宽度按 maxAbs 比例

### 4.12 ErrorPanel (错误日志)
- 默认折叠
- 点击展开: 红色 Console 字体
- 计数 Badge

### 4.13 LoadingOverlay
- 全屏半透明遮罩
- 旋转动画
- 进度文本

### 4.14 TabBar (底部导航)
- 高度: 56px (+ Safe Area)
- 两个Tab: Dashboard | Raw Data
- 选中态高亮

---

## 5. 交互设计

| 交互 | 实现 |
|------|------|
| 自动刷新 | 每60s 静默 GET /api/data，不显示loading |
| 手动刷新 | 点击刷新按钮 → showLoading → GET /api/data |
| 下拉刷新 | 未实现 Phase 1 (WebGL 触摸事件复杂) |
| 加载状态 | 全屏半透明 LoadingOverlay + spinner + 进度文字 |
| 错误处理 | StatusBar 灯变红，ErrorPanel 显示错误详情 |
| 空数据 | 显示 "--" 或 "No Data"，不崩溃 |
| 缓存指示 | StatusBar 显示 Cache Hit (绿) / Miss (黄) |
| Tab切换 | 底部 TabBar，Dashboard/Raw Data 切换 |
| Raw Data | Markdown 文本展示，可复制按钮 |

---

## 6. C# 类架构

### 6.1 数据模型 (MarketDataModels.cs)

```csharp
[Serializable]
public class MarketMeta { timestamp, fetch_seconds, cache_hit, errors[], data_sources[] }

[Serializable]
public class QuoteData { symbol, name, price, change, change_pct, day_high, day_low, volume, ... }

[Serializable]
public class FinvizData { rsi_14, atr_14, sma20_pct, sma50_pct, sma200_pct, perf_week, ... }

[Serializable]
public class ScoreData { signal, bullish_pct, bearish_pct, weighted_score, indicators[] }

[Serializable]
public class IndicatorScore { name, value, score, bear_pct, bull_pct, detail }

[Serializable]
public class SentimentData { score, rating, prev_close, prev_1_week, prev_1_month, prev_1_year }

[Serializable]
public class AaiiData { date, bullish, neutral, bearish, bull_bear_spread }

[Serializable]
public class DarkPoolData { off_exchange_pct, lit_pct, off_exchange_volume, avg_off_exchange_30d, signal }

[Serializable]
public class BreadthData { signal, advance_ratio, nyse_advance_decline, nyse_index }

[Serializable]
public class COTEntry { comm_name, as_of_date, asset_manager, leveraged_fund, dealer, total_oi }

[Serializable]
public class SectorEntry { name, price, change_pct }

[Serializable]
public class MarketData {
    MarketMeta meta;
    Dictionary<string, QuoteData> tickers;
    Dictionary<string, FinvizData> finviz;
    Dictionary<string, QuoteData> macro;
    SentimentData sentiment;
    Dictionary<string, ScoreData> scores;
    Dictionary<string, QuoteData> fred;
    AaiiData aaii;
    Dictionary<string, DarkPoolData> dark_pool;
    Dictionary<string, COTEntry> cftc_cot;
    BreadthData market_breadth;
    Dictionary<string, SectorEntry> sectors;
    Dictionary<string, List<OHLCBar>> historical_prices;
}
```

### 6.2 核心脚本

| 脚本 | 职责 | 目录 |
|------|------|------|
| `DataManager.cs` | HTTP请求, JSON解析, 60s Timer, CORS处理 | Scripts/ |
| `UIController.cs` | 数据分发, 注册子组件, Update统一刷新 | Scripts/ |
| `TickerCardUI.cs` | 单张行情卡片渲染 | Scripts/Components/ |
| `ScoreCardUI.cs` | AI评分卡片 | Scripts/Components/ |
| `OHLCChartUI.cs` | Canvas绘制OHLC迷你图 | Scripts/Components/ |
| `TechnicalTableUI.cs` | 技术指标表 | Scripts/Components/ |
| `MacroGridUI.cs` | 宏观指标网格 | Scripts/Components/ |
| `SentimentPanelUI.cs` | 情绪面板 | Scripts/Components/ |
| `DarkPoolCardUI.cs` | 暗池卡片 | Scripts/Components/ |
| `COTTableUI.cs` | COT表格 | Scripts/Components/ |
| `BreadthPanelUI.cs` | 市场宽度 | Scripts/Components/ |
| `SectorPanelUI.cs` | 板块列表 | Scripts/Components/ |
| `StatusBarUI.cs` | 顶栏 | Scripts/Components/ |
| `ErrorPanelUI.cs` | 错误日志 | Scripts/Components/ |
| `LoadingOverlay.cs` | 加载层 | Scripts/Components/ |
| `TabBarUI.cs` | 底部Tab | Scripts/Components/ |
| `SafeAreaFitter.cs` | 刘海屏/底部安全区适配 | Scripts/Components/ |

### 6.3 Editor 脚本

| 脚本 | 职责 | 目录 |
|------|------|------|
| `SceneBuilder.cs` | 一键创建完整Canvas+ScrollView+所有Panel | Editor/ |

---

## 7. API 适配

### 7.1 Flask CORS 修改

```python
# app.py 添加
from flask_cors import CORS
CORS(app)  # 允许WebGL跨域请求
```

需要新增依赖: `Flask-Cors>=4.0`

### 7.2 UnityWebRequest 配置

```csharp
var req = UnityWebRequest.Get(API_URL);
req.SetRequestHeader("Accept", "application/json");
req.timeout = 30;
yield return req.SendWebRequest();
```

WebGL 构建时 API URL 使用相对路径 (同域部署) 或绝对路径 (开发时 localhost:5050)。

---

## 8. 项目实施步骤

### Phase 1: 基础框架 (当前)

1. ✅ **产品设计文档** (本文档)
2. 创建 Unity 项目目录结构
3. 编写 Editor SceneBuilder.cs (一键搭建场景)
4. 编写数据模型 (MarketDataModels.cs)
5. 编写 DataManager.cs (HTTP + JSON)
6. 编写 UIController.cs + StatusBarUI.cs
7. 编写 TickerCardUI.cs + ScoreCardUI.cs
8. 编写 OHLCChartUI.cs
9. 编写 TechnicalTableUI.cs
10. 编写 MacroGridUI.cs + SentimentPanelUI.cs
11. 编写 DarkPoolCardUI.cs + COTTableUI.cs
12. 编写 BreadthPanelUI.cs + SectorPanelUI.cs
13. 编写 ErrorPanelUI.cs + LoadingOverlay.cs + TabBarUI.cs
14. 修改 Flask app.py (CORS + 新增端口信息)
15. 测试: 启动 Flask → Unity WebGL Play → 验证数据渲染

### Phase 2: 优化

- 下拉刷新
- 数据历史存储
- 离线缓存
- 推送通知

---

## 9. 文件清单

```
D:/unity-project/quant_mobile_dashboard/
├── Assets/
│   ├── Editor/
│   │   └── SceneBuilder.cs              ← Editor脚本，一键搭建场景
│   ├── Scripts/
│   │   ├── DataManager.cs               ← HTTP客户端 + 定时器
│   │   ├── MarketDataModels.cs          ← 所有数据模型 (JSON→C#)
│   │   ├── UIController.cs              ← 主控制器
│   │   ├── Components/
│   │   │   ├── StatusBarUI.cs           ← 顶栏
│   │   │   ├── TickerCardUI.cs          ← 行情卡片
│   │   │   ├── ScoreCardUI.cs           ← AI评分
│   │   │   ├── OHLCChartUI.cs           ← K线迷你图
│   │   │   ├── TechnicalTableUI.cs      ← 技术表
│   │   │   ├── MacroGridUI.cs           ← 宏观网格
│   │   │   ├── SentimentPanelUI.cs      ← 情绪面板
│   │   │   ├── DarkPoolCardUI.cs        ← 暗池卡片
│   │   │   ├── COTTableUI.cs            ← COT表
│   │   │   ├── BreadthPanelUI.cs        ← 市场宽度
│   │   │   ├── SectorPanelUI.cs         ← 板块
│   │   │   ├── ErrorPanelUI.cs          ← 错误日志
│   │   │   ├── LoadingOverlay.cs        ← 加载层
│   │   │   ├── TabBarUI.cs              ← Tab栏
│   │   │   ├── SectionHeaderUI.cs       ← 区块标题
│   │   │   └── ColorHelper.cs           ← 颜色工具
│   │   └── SafeAreaFitter.cs            ← 安全区适配
│   └── Resources/
├── Packages/
│   └── manifest.json                    ← Unity 6 WebGL 配置
├── ProjectSettings/
│   ├── ProjectVersion.txt               ← Unity 6000.0.x
│   ├── EditorSettings.asset
│   └── ProjectSettings.asset
└── README.md
```

---

## 10. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-05-08 | 初始产品设计，Phase 1 全部组件规格定义 |
