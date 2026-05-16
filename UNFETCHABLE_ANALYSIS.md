# 不可获取数据源深度分析

> 逐项拆解阻碍类型，区分"付费墙"与"非付费墙"障碍，并针对 JS 渲染给出专门方案。

---

## 一、不可获取数据源清单（按阻碍类型分类）

### 1.1 JS 动态渲染（13项）— 非付费墙

| # | 数据 | 来源 | 具体阻碍 | 是否付费 |
|---|------|------|---------|---------|
| 1 | TradingView 技术指标页 | tradingview.com/symbols/AMEX-SPY/technicals | 页面内容由 JS 在浏览器中渲染，服务端返回的 HTML 仅含空占位符 `<div class="tv-technical-indicators">`，无实际数据 | 否 |
| 2 | VPVR (Volume Profile) | TradingView 图表 | 图表数据通过 WebSocket 实时推送，HTML 中无静态数据 | 否 |
| 3 | XLK vs XLU 板块轮动 | TradingView 比较图表 | 同 #1，JS 渲染 + WebSocket 数据流 | 否 |
| 4 | VIX 期限结构图表 | CBOE 官网 | 图表由 Highcharts JS 在客户端渲染，HTML 无数据 | 否 |
| 5 | Put/Call Ratio 图表 | CBOE 官网 | 同 #4，JS 渲染图表 | 否 |
| 6 | NH/NL Ratio | NYSE 官网 | 数据表格由 React/Vue 前端框架动态加载，HTML 仅含骨架 | 否 |
| 7 | Advance/Decline Ratio | NYSE 官网 | 同 #6，前端框架渲染 | 否 |
| 8 | Investing.com 图表 | investing.com | 全站使用 JS 框架（React），价格数据通过 XHR/Fetch 动态加载 | 否 |
| 9 | Google Finance | google.com/finance | 完全 JS 渲染，服务端 HTML 几乎为空 | 否 |
| 10 | ForexFactory 日历 | forexfactory.com | 日历表格由 JS 动态生成，HTML 无事件数据 | 否 |
| 11 | ETF.com 数据 | etf.com | 前端框架渲染，数据通过 API 调用后注入 DOM | 否 |
| 12 | Seeking Alpha 图表 | seekingalpha.com | 图表和指标由 JS 渲染，且含反爬检测 | 否（部分内容免费） |
| 13 | BarChart 期权数据 | barchart.com | 表格数据由 JS 渲染，HTML 仅含表头 | 否 |

### 1.2 付费墙 / 会员制（4项）

| # | 数据 | 来源 | 具体阻碍 | 是否付费 |
|---|------|------|---------|---------|
| 14 | GEX (Gamma Exposure) | SpotGamma, UnusualWhales | 核心数据需订阅 ($100-500/月) | 是 |
| 15 | AAII 情绪指数 | aaii.com | 会员制，非会员只能看延迟/摘要数据 | 是 |
| 16 | CTA Positioning | 专业数据终端 (CFTC COT) | 需通过 Bloomberg/Refinitiv 等专业终端 | 是 |
| 17 | ETF Fund Flows (精确日度) | FactSet, State Street | 精确日度数据需机构订阅 | 是 |

### 1.3 反爬/风控机制（2项）— 非付费墙

| # | 数据 | 来源 | 具体阻碍 | 是否付费 |
|---|------|------|---------|---------|
| 18 | Max Pain | OptionCharts.io | Cloudflare 5秒盾 + 行为检测，非浏览器访问直接拦截 | 否 |
| 19 | State Street SPY 报表 | ssga.com | 无直接 API，数据以 PDF 形式发布，需人工解析 | 否 |

---

## 二、阻碍类型统计

| 阻碍类型 | 数量 | 占比 |
|---------|------|------|
| JS 动态渲染 | 13 | 68% |
| 付费墙/会员制 | 4 | 21% |
| 反爬/风控 | 2 | 11% |
| **总计** | **19** | **100%** |

**关键发现**: 付费墙仅占 21%，**79% 的不可获取数据源于技术障碍而非付费**。

---

## 三、JS 渲染专项获取方案分析

### 3.1 方案矩阵

| 方案 | 原理 | 复杂度 | 成本 | 成功率 | 适用场景 |
|------|------|--------|------|--------|---------|
| **A. Playwright/CDP 浏览器自动化** | 启动真实 Chromium，执行 JS，提取渲染后 DOM | 中 | 中（内存+CPU） | 85-95% | 所有 JS 渲染页面 |
| **B. 逆向 API 端点** | 抓包分析 JS 调用的内部 API，直接请求 | 高 | 低 | 40-70% | 有公开内部 API 的站点 |
| **C. SSR/预渲染版本** | 寻找服务端渲染的 fallback 或缓存版本 | 低 | 低 | 20-40% | 部分支持 SSR 的站点 |
| **D. 移动端 API** | 使用 App 的 API 端点（通常 less protected） | 中 | 低 | 50-70% | 有移动 App 的服务 |
| **E. 第三方聚合 API** | 使用聚合数据的第三方服务（如 Alpha Vantage, Polygon） | 低 | 中（API Key） | 60-80% | 有对应 API 的数据 |
| **F. RSS/Feed 替代** | 使用 RSS feed 或邮件订阅获取数据 | 低 | 低 | 30-50% | 新闻/日历类数据 |

### 3.2 各方案详细分析

#### 方案 A: Playwright / CDP 浏览器自动化

**原理**: 启动 headless Chromium，让页面完整执行 JS，等待渲染完成后再提取 DOM。

**实现方式**:
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.tradingview.com/symbols/AMEX-SPY/technicals/")
    page.wait_for_selector("[data-name='RSI']")  # 等待 JS 渲染完成
    rsi = page.inner_text("[data-name='RSI'] .value")
```

**优点**:
- 成功率最高（85-95%）
- 几乎可处理任何 JS 渲染页面
- 可模拟真实用户行为（点击、滚动）

**缺点**:
- 资源消耗大（每个页面需 100-300MB 内存）
- 速度慢（页面加载 3-10s）
- 部分站点检测 headless 浏览器并拦截
- 需要额外安装浏览器二进制文件

**针对本项目的可行性**:
- TradingView: 高 — 技术指标页结构稳定，有明确 data-name 属性
- CBOE VIX 期限: 中 — 图表数据可能在 canvas 中，提取较复杂
- NYSE 广度: 中 — 表格结构稳定
- Investing.com: 中 — 全站 JS，但 DOM 结构可预测

**在本项目的实施成本**:
- 需新增 `playwright` 依赖 (~50MB)
- 首次运行需下载 Chromium (~150MB)
- 每个页面抓取耗时 5-15s
- 内存占用: 每并发页面 ~200MB

#### 方案 B: 逆向 API 端点

**原理**: 使用浏览器 DevTools Network 面板抓包，找到 JS 调用的内部 API，直接请求该 API。

**实现方式**:
```python
# 示例: TradingView 内部 API
# 从 Network 面板发现: 
# https://www.tradingview.com/market/get-quotes/?symbols=AMEX:SPY

import requests
resp = requests.get(
    "https://www.tradingview.com/market/get-quotes/",
    params={"symbols": "AMEX:SPY"},
    headers={"User-Agent": "...", "Referer": "https://www.tradingview.com/"}
)
```

**优点**:
- 速度快（API 响应 <1s）
- 资源消耗低
- 可批量请求

**缺点**:
- 需要人工抓包分析每个站点
- API 可能随时变更
- 部分 API 需要认证 token/session
- CORS/Referer 限制

**针对本项目的可行性**:
- TradingView: 中 — 有内部 API，但需 session token
- CBOE: 低 — 数据可能内嵌在 JS bundle 中，无独立 API
- NYSE: 低 — 数据可能通过 WebSocket 推送
- Investing.com: 中 — 有 XHR 端点，但需逆向

**在本项目的实施成本**:
- 每个站点需 1-2 小时抓包分析
- API 变更后需重新分析
- 需维护 session/cookie 状态

#### 方案 C: SSR / 预渲染版本

**原理**: 寻找服务端渲染的 fallback 页面，或使用搜索引擎缓存、archive.org 等预渲染版本。

**实现方式**:
```python
# Google Web Cache
url = "https://webcache.googleusercontent.com/search?q=tradingview+spy+technicals"

# archive.org
url = "https://webcache.googleusercontent.com/search?q=cache:tradingview.com/symbols/AMEX-SPY/technicals"
```

**优点**:
- 无需额外工具
- 速度快

**缺点**:
- 数据延迟（缓存版本）
- 成功率低（很多站点禁止缓存）
- 数据可能不完整

**针对本项目的可行性**:
- TradingView: 低 — 禁止搜索引擎缓存
- CBOE: 低 — 动态数据不缓存
- 整体: 不推荐作为主要方案

#### 方案 D: 移动端 API

**原理**: 很多站点的移动 App 使用独立的 API 端点，保护程度低于网页版。

**实现方式**:
```python
# 使用 mitmproxy 抓包手机 App，找到 API 端点
# 或使用已知的公开移动 API

# 示例: Yahoo Finance 移动 API (与网页版不同)
# https://query1.finance.yahoo.com/v10/finance/quoteSummary/SPY?modules=...
```

**优点**:
- 通常 less protected
- 数据格式规整（JSON）

**缺点**:
- 需要抓包分析
- API 可能随时变更
- 需要模拟移动设备 headers

**针对本项目的可行性**:
- TradingView: 中 — 有移动 App，API 需抓包
- Investing.com: 中 — 有移动 App
- 整体: 可作为补充方案

#### 方案 E: 第三方聚合 API

**原理**: 使用提供相同数据的第三方 API 服务。

**可用服务**:
| 服务 | 数据 | 免费额度 | 费用 |
|------|------|---------|------|
| Alpha Vantage | 股票/外汇/加密货币 | 25 calls/day | $49.99/月 |
| Polygon.io | 股票/期权/外汇 | 5 API calls/min | $199/月 |
| Finnhub | 股票/外汇/加密货币 | 60 calls/min | 付费升级 |
| IEX Cloud | 股票/ETF | 50K messages/mo | 付费升级 |
| Quandl/NASDAQ Data Link | 宏观经济 | 有限 | 付费 |
| CBOE LiveVol API | 期权/GEX/VIX | 无免费 | 付费 |
| SpotGamma API | GEX/Max Pain | 无免费 | $100-500/月 |

**优点**:
- 数据规整，API 稳定
- 文档完善

**缺点**:
- 免费额度极低
- 付费版本成本高
- 数据可能有延迟

**针对本项目的可行性**:
- GEX/Max Pain: 低 — 仅 SpotGamma/CBOE 提供，均需付费
- VIX 期限: 低 — 无免费 API
- 技术指标: 中 — Alpha Vantage 提供部分指标（RSI/MACD/SMA）
- 市场广度: 低 — 无免费 API

#### 方案 F: RSS / Feed 替代

**原理**: 使用 RSS feed、邮件订阅或 Twitter/X API 获取数据更新。

**可用源**:
- CBOE RSS: https://www.cboe.com/us/news/rss.xml
- ForexFactory RSS: 部分数据可通过 RSS 获取
- Twitter/X API: 关注官方账号获取数据发布

**优点**:
- 实时推送
- 无需渲染

**缺点**:
- 数据不完整
- 需要解析非结构化文本
- 依赖第三方平台政策

**针对本项目的可行性**:
- 经济日历: 中 — ForexFactory 有 RSS
- 政策新闻: 中 — 可通过 RSS/搜索获取
- 技术指标: 低 — 无 RSS 源

---

## 四、JS 渲染专项建议

### 4.1 优先级排序

| 优先级 | 数据 | 推荐方案 | 预期成功率 | 实施工作量 |
|--------|------|---------|-----------|-----------|
| P0 | TradingView 技术指标 | Playwright/CDP | 90% | 2-3h |
| P0 | Investing.com 数据 | Playwright/CDP | 80% | 2-3h |
| P1 | CBOE VIX 期限 | 逆向 API + Playwright fallback | 60% | 4-6h |
| P1 | Put/Call Ratio | 逆向 API + Playwright fallback | 50% | 4-6h |
| P2 | NYSE 广度 (NH/NL/A/D) | Playwright/CDP | 70% | 3-4h |
| P2 | BarChart 期权 | Playwright/CDP | 70% | 3-4h |
| P3 | ForexFactory 日历 | RSS + 固定推算 | 60% | 1-2h |
| P3 | Seeking Alpha | Playwright + 反爬绕过 | 40% | 4-6h |

### 4.2 技术实现建议

**推荐架构**: Playwright 作为 JS 渲染层，与现有 fetcher 并行

```
fetchers/
  ├── js_renderer.py          # Playwright 封装层
  ├── tradingview_fetcher.py  # TradingView 技术指标
  ├── investing_fetcher.py    # Investing.com 数据
  ├── cboe_fetcher.py         # CBOE VIX/期权
  └── nyse_breadth_fetcher.py # NYSE 市场广度
```

**js_renderer.py 核心设计**:
```python
from playwright.sync_api import sync_playwright

class JSRenderer:
    def __init__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
    
    def fetch(self, url: str, wait_selector: str, extract_fn) -> dict:
        page = self.browser.new_page()
        page.goto(url, wait_until="networkidle")
        page.wait_for_selector(wait_selector, timeout=10000)
        result = extract_fn(page)
        page.close()
        return result
    
    def close(self):
        self.browser.close()
        self.playwright.stop()
```

**资源管理**:
- 使用连接池复用 browser context（减少内存开销）
- 限制并发数（建议 max 3-5 个页面同时渲染）
- 设置页面超时（10-15s）
- 失败自动重试（最多 2 次）

### 4.3 预期收益

实施 JS 渲染方案后，数据完整度预期提升:

| 阶段 | 完整度 | 新增数据 |
|------|--------|---------|
| 当前 (无 JS) | 47% | — |
| + TradingView 技术指标 | 55% | RSI/MACD/MA 多周期 |
| + Investing.com | 60% | 5日形态/图表数据 |
| + CBOE VIX 期限 | 63% | VIX term structure |
| + NYSE 广度 | 67% | NH/NL, A/D |
| + ForexFactory 日历 | 70% | 精确经济日历 |

**结论**: 实施 Playwright 方案可将数据完整度从 47% 提升至 **70%**，覆盖大部分 JS 渲染数据。剩余 30% 仍为付费墙/专业终端数据，无法通过技术手段解决。
