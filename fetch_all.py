"""
一键全量数据抓取 — fetch_all.py v2.0
===================================
覆盖全部可获取数据源（13 个 fetcher），输出统一 JSON 供分析层消费。

用法:
    python fetch_all.py                   # 抓取并打印摘要
    python fetch_all.py --output data.json # 保存到文件
    python fetch_all.py --quiet            # 仅输出 JSON (stdout)
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone

from fetchers.yahoo_fetcher import YahooFetcher
from fetchers.finviz_fetcher import FinvizFetcher
from fetchers.cnn_sentiment import get_fear_greed
from fetchers.fred_fetcher import get_all_fred
from fetchers.time_fetcher import get_edt_time
from fetchers.marketwatch_fetcher import get_marketwatch_quote
from fetchers.options_fetcher import get_vix_term_structure, get_put_call_ratio
from fetchers.econ_calendar import get_economic_calendar
from fetchers.aaii_fetcher import get_aaii_sentiment
from fetchers.dark_pool import get_dark_pool_summary
from fetchers.cftc_cot import get_cot_all
from fetchers.market_breadth import get_market_breadth, get_sector_performance

from config import TICKERS, MACRO_SYMBOLS, REQUEST_TIMEOUT

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("fetch-all")

yahoo = YahooFetcher()
finviz = FinvizFetcher()


def fetch_edt_time() -> dict:
    try:
        return get_edt_time()
    except Exception as exc:
        return {"error": str(exc), "source": "time.is"}


def fetch_tickers() -> dict:
    result = {}
    errors = []
    try:
        all_syms = TICKERS + list(MACRO_SYMBOLS.keys()) + ["HYG", "JNK"]
        raw = yahoo.get_quotes(all_syms)
        by_sym = {q.get("symbol", ""): q for q in raw}
    except Exception as exc:
        logger.exception("Yahoo failed")
        errors.append(f"Yahoo: {exc}")
        by_sym = {}
    for ticker in TICKERS:
        q = by_sym.get(ticker)
        result[ticker] = _norm_quote(q) if q else {"symbol": ticker, "error": "no_yahoo_data"}
    try:
        for ticker in TICKERS:
            mw = get_marketwatch_quote(ticker)
            if mw and mw.get("price"):
                result[ticker]["mw_verify"] = mw
    except Exception as exc:
        logger.warning("MW verify: %s", exc)
    macro_raw = {}
    for sym, name in MACRO_SYMBOLS.items():
        q = by_sym.get(sym)
        macro_raw[name] = _norm_quote(q) if q else {"error": "no_data"}
    credit_raw = {}
    for sym in ("HYG", "JNK"):
        q = by_sym.get(sym)
        credit_raw[sym] = _norm_quote(q) if q else {"error": "no_data"}
    return {"tickers": result, "macro": macro_raw, "credit": credit_raw, "errors": errors}


def fetch_technicals() -> dict:
    finviz_data, yahoo_data, errors = {}, {}, []
    for ticker in TICKERS:
        try:
            tech = finviz.get_technicals(ticker)
            if tech:
                finviz_data[ticker] = tech
            else:
                errors.append(f"Finviz: {ticker} N/A")
        except Exception as exc:
            errors.append(f"Finviz: {ticker} -> {exc}")
        try:
            yd = yahoo.fetch_ticker_data(ticker)
            if yd:
                yahoo_data[ticker] = yd
        except Exception as exc:
            errors.append(f"Yahoo tech: {ticker} -> {exc}")
    return {"finviz": finviz_data, "yahoo": yahoo_data, "errors": errors}


def fetch_sentiment() -> dict:
    try:
        fg = get_fear_greed()
        return {"cnn_fear_greed": fg} if fg else {"cnn_fear_greed": None, "error": "empty"}
    except Exception as exc:
        return {"cnn_fear_greed": None, "error": str(exc)}


def fetch_fred_data() -> dict:
    try:
        return get_all_fred()
    except Exception as exc:
        return {"error": str(exc)}


def fetch_options_data() -> dict:
    result = {"vix_term_structure": None, "put_call_ratio": None, "errors": []}
    try:
        vts = get_vix_term_structure()
        result["vix_term_structure"] = vts if vts else None
        if not vts:
            result["errors"].append("VIX term: N/A")
    except Exception as exc:
        result["errors"].append(f"VIX term: {exc}")
    try:
        pcr = get_put_call_ratio()
        result["put_call_ratio"] = pcr if pcr else None
        if not pcr:
            result["errors"].append("P/C Ratio: N/A")
    except Exception as exc:
        result["errors"].append(f"P/C Ratio: {exc}")
    return result


def fetch_economic_calendar() -> dict:
    try:
        events = get_economic_calendar()
        return {"events": events} if events else {"events": [], "error": "empty"}
    except Exception as exc:
        return {"events": [], "error": str(exc)}


def fetch_aaii() -> dict:
    try:
        d = get_aaii_sentiment()
        return d if d else {"error": "empty"}
    except Exception as exc:
        return {"error": str(exc)}


def fetch_dark_pool() -> dict:
    result = {}
    errors = []
    for ticker in TICKERS:
        try:
            dp = get_dark_pool_summary(ticker)
            result[ticker] = dp if dp else {"error": "empty"}
        except Exception as exc:
            result[ticker] = {"error": str(exc)}
            errors.append(f"DP[{ticker}]: {exc}")
    return {k: v for k, v in result.items()} if not all(v.get("error") for v in result.values()) else {"error": "all_failed"}


def fetch_cot() -> dict:
    try:
        return get_cot_all()
    except Exception as exc:
        return {"error": str(exc)}


def fetch_breadth() -> dict:
    try:
        return get_market_breadth()
    except Exception as exc:
        return {"error": str(exc)}


def fetch_sectors() -> dict:
    try:
        return get_sector_performance()
    except Exception as exc:
        return {"error": str(exc)}


def build_completeness_report(all_data: dict) -> dict:
    report = {"categories": {}, "overall_pct": 0, "missing_critical": [], "impossible_no_fix": []}
    checks = [
        ("edt_time",     ["edt_time"]),
        ("price_all",    ["tickers.SPY", "tickers.GDXU", "tickers.SOXX"]),
        ("macro",        ["macro.VIX", "macro.DXY", "macro.US10Y", "macro.GOLD"]),
        ("credit",       ["credit.HYG", "credit.JNK"]),
        ("rsi_atr_sma",  ["technicals_finviz.SPY.rsi_14", "technicals_finviz.GDXU.rsi_14", "technicals_finviz.SOXX.rsi_14"]),
        ("sentiment",    ["sentiment.cnn_fear_greed"]),
        ("fred",         ["fred.VIX", "fred.TIPS"]),
        ("calendar",     ["calendar"]),
        ("aaii",         ["aaii.bullish"]),
        ("dark_pool",    ["dark_pool.SPY.off_exchange_pct"]),
        ("cftc_cot",     ["cftc_cot.138741"]),
        ("breadth",      ["market_breadth.signal"]),
        ("sectors",      ["sectors.XLK"]),
    ]

    impossible = [
        ("GEX (Gamma Exposure)",   "付费/JS渲染, 需 Playwright (optionsgex.com/titangex.com)"),
        ("Max Pain",               "JS渲染 (maximum-pain.com/optioncharts.io)"),
        ("VPVR (Volume Profile)",  "可从 OHLCV 计算, 已注释"),
        ("VIX Term Structure",     "vixcentral.com JS渲染, CBOE需playwright"),
        ("ETF Fund Flows (精确)",  "专业数据, 当前用代理 (Yahoo AUM推断+OBV)"),
    ]
    report["impossible_no_fix"] = [{"item": n, "reason": r} for n, r in impossible]

    fetched, total = 0, 0
    for cat, paths in checks:
        total += 1
        all_ok = True
        for path in paths:
            val = _deep_get(all_data, path.split("."))
            if val is None or (isinstance(val, dict) and val.get("error")) or (isinstance(val, list) and len(val) == 0):
                all_ok = False
                report["missing_critical"].append(path)
        if all_ok:
            fetched += 1
        report["categories"][cat] = {"complete": all_ok, "paths": paths}
    report["overall_pct"] = round(fetched / total * 100) if total else 0
    report["fetched_categories"] = fetched
    report["total_categories"] = total
    report["impossible_count"] = len(impossible)
    return report


def _deep_get(d: dict, keys: list):
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return None
    return d


def _norm_quote(q: dict) -> dict:
    if q is None:
        return {"error": "null_quote"}
    return {
        "symbol": q.get("symbol"), "name": q.get("shortName") or q.get("longName", ""),
        "price": q.get("regularMarketPrice"), "change": q.get("regularMarketChange"),
        "change_pct": q.get("regularMarketChangePercent"),
        "day_high": q.get("regularMarketDayHigh"), "day_low": q.get("regularMarketDayLow"),
        "prev_close": q.get("regularMarketPreviousClose"),
        "week52_high": q.get("fiftyTwoWeekHigh"), "week52_low": q.get("fiftyTwoWeekLow"),
        "volume": q.get("regularMarketVolume"), "avg_volume": q.get("averageDailyVolume3Month"),
        "ma_50": q.get("fiftyDayAverage"), "ma_200": q.get("twoHundredDayAverage"),
        "beta": q.get("beta"), "market_cap": q.get("marketCap"),
        "nav_price": q.get("navPrice"), "total_assets": q.get("totalAssets"),
        "market_state": q.get("marketState", "UNKNOWN"),
    }


def fetch_all() -> dict:
    started = time.time()
    timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tasks = {
        "edt_time": fetch_edt_time, "price_macro_credit": fetch_tickers,
        "technicals": fetch_technicals, "sentiment": fetch_sentiment,
        "fred": fetch_fred_data, "options_data": fetch_options_data,
        "calendar": fetch_economic_calendar, "aaii": fetch_aaii,
        "dark_pool": fetch_dark_pool, "cftc_cot": fetch_cot,
        "market_breadth": fetch_breadth, "sectors": fetch_sectors,
    }
    results, errors_all = {}, []
    logger.info("=== 全量数据抓取 v2.0 (13 fetchers) ===")
    for name, fn in tasks.items():
        t0 = time.time()
        try:
            results[name] = fn()
            elapsed = round(time.time() - t0, 2)
            if isinstance(results[name], dict):
                for e in results[name].get("errors", []):
                    errors_all.append(f"[{name}] {e}")
            logger.info("  %-20s OK  %.2fs", name, elapsed)
        except Exception as exc:
            results[name] = {"error": str(exc)}
            errors_all.append(f"[{name}] {exc}")
            logger.error("  %-20s FAIL  %s", name, exc)

    ticker_res = results.get("price_macro_credit", {})
    tech_res = results.get("technicals", {})
    cal_res = results.get("calendar", {})

    all_data = {
        "fetch_meta": {
            "timestamp": timestamp_utc,
            "duration_seconds": round(time.time() - started, 2),
            "errors": errors_all,
            "source_count": len(tasks),
        },
        "edt_time":           results.get("edt_time", {}),
        "tickers":            ticker_res.get("tickers", {}),
        "macro":              ticker_res.get("macro", {}),
        "credit":             ticker_res.get("credit", {}),
        "technicals_finviz":  tech_res.get("finviz", {}),
        "technicals_yahoo":   tech_res.get("yahoo", {}),
        "sentiment":          results.get("sentiment", {}),
        "fred":               results.get("fred", {}),
        "options_data":       results.get("options_data", {}),
        "calendar":           cal_res.get("events", []),
        "aaii":               results.get("aaii", {}),
        "dark_pool":          results.get("dark_pool", {}),
        "cftc_cot":           results.get("cftc_cot", {}),
        "market_breadth":     results.get("market_breadth", {}),
        "sectors":            results.get("sectors", {}),
    }
    all_data["data_completeness"] = build_completeness_report(all_data)
    return all_data


def print_summary(data: dict):
    meta = data["fetch_meta"]
    dc = data.get("data_completeness", {})
    edt = data.get("edt_time", {})
    print("\n" + "=" * 78)
    print("  Quant Data Fetcher v2.0 -- 全量数据抓取报告")
    print("=" * 78)
    print(f"\n  [TIME] EDT: {edt.get('edt_datetime','N/A')} ({edt.get('session_label','?')}) | UTC: {meta['timestamp']} | {meta['duration_seconds']}s")

    # Quotess
    print(f"\n  {'-'*60}\n  [QUOTES]")
    for sym, q in data.get("tickers", {}).items():
        if q.get("error"):
            print(f"  {sym:6s} ERROR: {q.get('error')}")
        else:
            cp = q.get("change_pct", 0) or 0
            print(f"  {sym:6s} ${q.get('price','?'):>10,.2f}  {'+' if cp>=0 else ''}{cp:.2f}%  Vol: {_fmt_vol(q.get('volume'))}")

    # Tech
    print(f"\n  {'-'*60}\n  [TECH] Finviz")
    tf = data.get("technicals_finviz", {})
    for key, label in [("rsi_14","RSI(14)"),("atr_14","ATR(14)"),("sma20_pct","SMA20%"),("sma50_pct","SMA50%"),("sma200_pct","SMA200%"),("perf_week","W"),("perf_month","M"),("perf_ytd","YTD"),("perf_year","1Y")]:
        row = f"  {label:<10s}"
        for sym in TICKERS:
            v = tf.get(sym,{}).get(key,"--")
            row += f" {v:>10}" if isinstance(v, str) else f" {v:>10.2f}"
        print(row)

    # Macro
    print(f"\n  {'-'*60}\n  [MACRO]")
    for name, q in data.get("macro", {}).items():
        if q and not q.get("error"):
            print(f"  {name:8s} {q.get('price','?'):>10,.2f}")
    for sym, q in data.get("credit", {}).items():
        if q and not q.get("error"):
            print(f"  {sym:8s} {q.get('price','?'):>10,.2f}")

    # Sentiment
    print(f"\n  {'-'*60}\n  [SENT]")
    fg = data.get("sentiment", {}).get("cnn_fear_greed")
    if fg:
        print(f"  CNN F&G: {fg.get('score','?')} ({fg.get('rating','?')})")
    else:
        print(f"  CNN: N/A")
    aaii = data.get("aaii", {})
    if aaii.get("bullish"):
        print(f"  AAII: Bull={aaii['bullish']}% Bear={aaii['bearish']}% Spread={aaii.get('bull_bear_spread','?')}")
    else:
        print(f"  AAII: N/A")

    # Dark Pool
    print(f"\n  {'-'*60}\n  [DARK POOL]")
    dp = data.get("dark_pool", {})
    for sym, d in dp.items():
        if d.get("off_exchange_pct"):
            print(f"  {sym:6s} DP={d['off_exchange_pct']}% Lit={d.get('lit_pct','?')}% 30dAvg={d.get('avg_off_exchange_30d','?')}% Signal: {d.get('signal','?')}")
        else:
            print(f"  {sym:6s} N/A")

    # COT
    print(f"\n  {'-'*60}\n  [CFTC COT]")
    cot = data.get("cftc_cot", {})
    es = cot.get("138741")
    if es:
        print(f"  {es['comm_name']} ({es['as_of_date']}): AM={es['asset_manager']['net']:+,} LF={es['leveraged_fund']['net']:+,} DL={es['dealer']['net']:+,} OI={es['total_oi']:,}")
    else:
        print("  ES: N/A")

    # Breadth
    print(f"\n  {'-'*60}\n  [BREADTH]")
    mb = data.get("market_breadth", {})
    print(f"  Signal: {mb.get('signal','?')}")
    ad = mb.get("nyse_advance_decline")
    if ad:
        print(f"  Adv/Dec: {ad.get('advances','?')}/{ad.get('declines','?')} ratio={mb.get('advance_ratio','?')}")

    # Sectors
    print(f"\n  {'-'*60}\n  [SECTORS]")
    sectors = data.get("sectors", {})
    items = sorted(sectors.items(), key=lambda x: x[1].get("change_pct") or 0, reverse=True)
    for sym, s in items[:6]:
        print(f"  {sym:6s} {s.get('name',''):20s} {s.get('change_pct',0):>+.2f}%")

    # Calendar
    print(f"\n  {'-'*60}\n  [CALENDAR]")
    for ev in data.get("calendar", [])[:5]:
        try:
            print(f"  {ev.get('date','')} {ev.get('time',''):>8s} {ev.get('event','')} {ev.get('impact','')}")
        except UnicodeEncodeError:
            pass

    # Errors
    if meta.get("errors"):
        print(f"\n  {'-'*60}\n  [ERRORS] ({len(meta['errors'])} items)")
        for e in meta["errors"]:
            print(f"  - {e}")

    # Completeness
    print(f"\n  {'='*60}\n  [COMPLETENESS] 获取: {dc.get('fetched_categories',0)}/{dc.get('total_categories',0)} ({dc.get('overall_pct',0)}%)")
    missing = dc.get("missing_critical", [])
    if missing:
        print(f"  Missing: {missing}")
    for imp in dc.get("impossible_no_fix", []):
        print(f"  ! {imp['item']:40s} | {imp['reason']}")


def _fmt_vol(v):
    if v is None: return "--"
    n = float(v)
    if n >= 1e9: return f"{n/1e9:.2f}B"
    if n >= 1e6: return f"{n/1e6:.2f}M"
    if n >= 1e3: return f"{n/1e3:.1f}K"
    return f"{n:.0f}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quant Data Fetcher v2.0 -- 全量抓取")
    parser.add_argument("--output", "-o", help="JSON 输出路径")
    parser.add_argument("--quiet", "-q", action="store_true", help="仅 JSON")
    parser.add_argument("--summary-only", "-s", action="store_true", help="仅摘要")
    args = parser.parse_args()
    data = fetch_all()
    if not args.quiet:
        print_summary(data)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        logger.info("Saved -> %s", args.output)
    elif args.summary_only:
        pass
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
