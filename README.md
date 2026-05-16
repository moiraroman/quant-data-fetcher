# Quant Data Fetcher — 系统化量化数据抓取平台

> **数据获取层**（独立于分析层）— 为后期量化分析提供标准化数据输入。

## 架构

```
quant_data_fetcher/
├── app.py                      # Flask 主程序 (API + 路由)
├── config.py                   # 配置中心 (标的、数据源、缓存)
├── requirements.txt            # Python 依赖
├── fetchers/
│   ├── __init__.py
│   ├── yahoo_fetcher.py        # Yahoo Finance → 实时行情 + 均线
│   ├── finviz_fetcher.py       # Finviz → RSI/ATR/SMA/多周期收益率
│   ├── cnn_sentiment.py        # CNN → Fear & Greed 情绪指数
│   └── fred_fetcher.py         # FRED → VIX/利率/美元指数经济数据
├── templates/
│   └── index.html              # Web Dashboard UI
└── static/
    ├── style.css               # 暗色主题样式
    └── app.js                  # 前端渲染 + 60s 自动刷新
```

## 数据源 & 能力矩阵

| 数据源 | 方式 | 覆盖内容 |
|--------|------|---------|
| **Yahoo Finance** | v7 Quote API + Cookie/Crumb | 实时价格、涨跌幅、日内区间、52周区间、成交量、MA50/MA200、Beta、NAV、AUM |
| **Finviz** | HTML 解析 (BS4) | RSI(14)、ATR(14)、SMA20/50/200偏离%、周/月/季/半年/YTD/年收益、RelVol、AUM |
| **CNN Fear & Greed** | JSON API | 情绪得分(0-100)、评级(恐惧/贪婪)、历史均值 |
| **FRED** | Graph CSV Endpoint | VIX收盘值、美债利率、美元贸易加权指数 (T-1延迟) |

## 数据聚合能力

单次 `/api/data` 调用自动合并 4 个数据源，返回统一 JSON：

```json
{
  "meta": {
    "timestamp": "2026-05-05T17:15:56Z",
    "fetch_seconds": 4.91,
    "errors": [],
    "data_sources": ["yahoo", "finviz", "cnn", "fred"]
  },
  "tickers": { "SPY": {...}, "GDXU": {...}, "SOXX": {...} },
  "finviz":  { "SPY": { "rsi_14": 71.1, "atr_14": 7.60, ... }, ... },
  "macro":   { "VIX": {...}, "DXY": {...}, "US10Y": {...}, "GOLD": {...} },
  "sentiment": { "score": 67.14, "rating": "greed", ... },
  "fred":    { "VIX": { "latest_value": 18.29, "latest_date": "2026-05-04" } }
}
```

## 快速启动

```bash
# 1. 进入项目目录
cd quant_data_fetcher

# 2. 安装依赖 (requests, beautifulsoup4, flask 已预装则跳过)
pip install -r requirements.txt

# 3. 启动
python app.py

# 4. 打开浏览器
# http://127.0.0.1:5050
```

## API 端点

| 端点 | 用途 |
|------|------|
| `GET /` | Web Dashboard |
| `GET /api/data` | 获取全量数据 (60s 缓存) |
| `GET /api/refresh` | 强制刷新 + 返回 |
| `GET /api/health` | 健康检查 |

## 扩展方式

### 新增标的
修改 `config.py` → `TICKERS` 列表，重启即可。

### 新增数据源
1. 在 `fetchers/` 新建模块
2. 在 `app.py` 的 `_build_data()` 中调用
3. 前端 `app.js` 中新增渲染函数

### 供分析层消费
```python
import requests
data = requests.get("http://127.0.0.1:5050/api/data").json()
# 直接使用 data["tickers"]["SPY"]["price"] 等字段
```

## 设计原则

- **零外部 API Key 依赖** — 全部使用公开免费数据端点
- **容错设计** — 单个数据源失败不影响其他源
- **限速保护** — Finviz 内置请求间隔，Yahoo 自动管理 Crumb
- **缓存策略** — 60s TTL 避免 API 限流，前端自动刷新
