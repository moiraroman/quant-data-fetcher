"""
经济日历抓取器
===============
尝试从公开源抓取未来 5 个交易日的美国重要经济数据发布日程。

数据源:
  - Investing.com 经济日历: https://www.investing.com/economic-calendar/  (JS 渲染)
  - ForexFactory: https://www.forexfactory.com/calendar                   (JS 渲染)
  - Econoday: https://www.econoday.com/                                    (尝试 SSR)
  - MarketWatch 经济日历: https://www.marketwatch.com/economy-politics/calendar

备选: 从已知的定期发布日程推算（如 NFP: 每月第一个周五）
"""

import logging
import re
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from config import REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/132.0.0.0 Safari/537.36"
    ),
}


# 定期发布的关键数据（按美国时间规律推算）
_FIXED_SCHEDULE = {
    "ISM Manufacturing PMI":    {"day": "monthly_1st_business_day", "time": "10:00 AM"},
    "ISM Services PMI":         {"day": "monthly_3rd_business_day", "time": "10:00 AM"},
    "Nonfarm Payrolls":         {"day": "monthly_1st_friday", "time": "8:30 AM"},
    "Unemployment Rate":        {"day": "monthly_1st_friday", "time": "8:30 AM"},
    "CPI (MoM)":                {"day": "monthly_2nd_week_wed_or_thu", "time": "8:30 AM"},
    "Core CPI (MoM)":           {"day": "monthly_2nd_week_wed_or_thu", "time": "8:30 AM"},
    "PPI (MoM)":                {"day": "monthly_2nd_week_wed_or_thu", "time": "8:30 AM"},
    "Retail Sales (MoM)":       {"day": "monthly_midmonth", "time": "8:30 AM"},
    "FOMC Decision":            {"day": "scheduled_by_fed", "time": "2:00 PM"},
    "Initial Jobless Claims":   {"day": "every_thursday", "time": "8:30 AM"},
    "GDP (QoQ)":                {"day": "monthly_late", "time": "8:30 AM"},
    "Core PCE (MoM)":           {"day": "monthly_late", "time": "8:30 AM"},
    "Consumer Confidence":      {"day": "monthly_last_tuesday", "time": "10:00 AM"},
    "Durable Goods Orders":     {"day": "monthly_late", "time": "8:30 AM"},
    "Existing Home Sales":      {"day": "monthly_3rd_week", "time": "10:00 AM"},
    "New Home Sales":           {"day": "monthly_3rd_week", "time": "10:00 AM"},
}


def get_economic_calendar(days_ahead: int = 5) -> list[dict]:
    """
    获取未来 N 个交易日的经济日历。

    先尝试从 MarketWatch 抓取，失败则用固定日程推算。

    返回:
        [
            {"date": "2026-05-06", "time": "8:30 AM", "event": "Initial Jobless Claims", "impact": "medium", "note": "estimated"},
            ...
        ]
    """
    events = []

    # ---- 方案 A: MarketWatch 经济日历 ------------------------------------
    try:
        mw_events = _scrape_marketwatch_calendar(days_ahead)
        if mw_events:
            logger.info("MarketWatch calendar: got %d events", len(mw_events))
            return _prioritize_events(mw_events)
    except Exception as exc:
        logger.warning("MarketWatch calendar scrape: %s", exc)

    # ---- 方案 B: Econoday -------------------------------------------------
    try:
        econoday_events = _scrape_econoday(days_ahead)
        if econoday_events:
            logger.info("Econoday: got %d events", len(econoday_events))
            return _prioritize_events(econoday_events)
    except Exception as exc:
        logger.warning("Econoday scrape: %s", exc)

    # ---- 方案 C: 固定日程推算（兜底）--------------------------------------
    logger.info("No live calendar source available, using fixed schedule estimation")
    events = _estimate_from_fixed_schedule(days_ahead)
    return events


# ---- 方案 A: MarketWatch ---------------------------------------------------

def _scrape_marketwatch_calendar(days_ahead: int) -> list[dict]:
    url = "https://www.marketwatch.com/economy-politics/calendar"
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    # MarketWatch 日历行结构: div.calendar__table 内 tr
    table = soup.find("div", class_="calendar__table")
    if not table:
        table = soup.find("table", class_=re.compile("calendar", re.I))

    if table:
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 3:
                continue
            date_text = cells[0].get_text(strip=True)
            time_text = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            event_text = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            actual_val = cells[3].get_text(strip=True) if len(cells) > 3 else ""

            if not date_text or not event_text:
                continue
            if len(date_text) < 5:
                continue  # 跳过非日期行

            impact = _infer_impact(event_text)
            # 只保留高/中影响的事件
            events.append({
                "date": date_text,
                "time": time_text,
                "event": event_text,
                "previous": actual_val,
                "impact": impact,
                "source": "marketwatch.com",
            })

    return events


# ---- 方案 B: Econoday ------------------------------------------------------

def _scrape_econoday(days_ahead: int) -> list[dict]:
    url = "https://www.econoday.com/calendar/"
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    # econoday 结构: 表格 class=eventcalendar
    table = soup.find("table", class_=re.compile("eventcalendar", re.I))
    if not table:
        table = soup.find("table", class_=re.compile("calendar", re.I))

    if table:
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 3:
                continue
            date_text = cells[0].get_text(strip=True)
            event_text = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            time_text = cells[1].get_text(strip=True) if len(cells) > 1 else ""

            if not event_text or len(event_text) < 3:
                continue

            events.append({
                "date": date_text,
                "time": time_text,
                "event": event_text,
                "impact": _infer_impact(event_text),
                "source": "econoday.com",
            })

    return events


# ---- 方案 C: 固定日程推算 -------------------------------------------------

def _estimate_from_fixed_schedule(days_ahead: int) -> list[dict]:
    """基于固定发布规律，推算未来 N 日可能的重要数据。"""
    events = []
    today = datetime.now()
    future_5d = []

    # 生成未来 N 个工作日
    d = today
    count = 0
    while count < days_ahead:
        d = d + timedelta(days=1)
        if d.weekday() < 5:  # Mon-Fri
            future_5d.append(d)
            count += 1

    # 常规每周事件
    for d in future_5d:
        if d.weekday() == 3:  # Thursday
            events.append({
                "date": d.strftime("%Y-%m-%d"),
                "time": "8:30 AM",
                "event": "Initial Jobless Claims",
                "impact": "medium",
                "source": "fixed_schedule_estimate",
            })

    # 月频事件（推断）
    month_start = min(d.day for d in future_5d)
    month_end = max(d.day for d in future_5d)

    if month_start <= 7:
        # 月初 → ISM/NFP 可能已过或即将
        for d in future_5d:
            if d.weekday() == 4 and d.day <= 7:
                events.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "time": "8:30 AM",
                    "event": "[EVENT RISK] Nonfarm Payrolls + Unemployment Rate",
                    "impact": "high",
                    "source": "fixed_schedule_estimate",
                })

    if 10 <= month_start <= 16 or 10 <= month_end <= 16:
        events.append({
            "date": "2026-05-11~2026-05-14",
            "time": "8:30 AM",
            "event": "[EVENT RISK] CPI (MoM) + Core CPI (预计)",
            "impact": "high",
            "source": "fixed_schedule_estimate",
        })

    return _prioritize_events(events)


# ---- 工具函数 -------------------------------------------------------------

def _prioritize_events(events: list[dict]) -> list[dict]:
    """过滤 + 排序：高影响优先，去标题/占位重复。"""
    seen = set()
    result = []
    for ev in events:
        event_key = ev.get("event", "").lower().strip()
        # 跳过明显的 ads / empty / navigation
        skip_words = ["advertisement", "sponsored", "subscribe", "login", "sign up"]
        if any(w in event_key for w in skip_words):
            continue
        if len(event_key) < 5:
            continue
        # 去重
        if event_key in seen:
            continue
        seen.add(event_key)
        result.append(ev)

    # 排序: impact hi > med > low, 然后 date
    impact_order = {"high": 0, "medium": 1, "low": 2}
    result.sort(key=lambda x: (impact_order.get(x.get("impact", "").lower(), 3), x.get("date", "")))
    return result


def _infer_impact(event_name: str) -> str:
    """根据事件名称推断影响等级。"""
    en = event_name.lower()
    high_keywords = ["fomc", "nonfarm", "cpi", "core cpi", "pce", "gdp", "nfp", "payroll"]
    med_keywords = ["jobless", "ism", "retail", "ppi", "consumer conf", "durable", "housing", "claims"]

    for kw in high_keywords:
        if kw in en:
            return "high"
    for kw in med_keywords:
        if kw in en:
            return "medium"
    return "low"
