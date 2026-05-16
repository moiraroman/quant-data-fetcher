"""
EDT 时间抓取器
===============
从 time.is 提取当前美东日期+时间，判断交易时段。
"""

import re
import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from config import REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

TIME_IS_URL = "https://time.is/New_York"

# 英文(含单字母缩写) 月名映射
_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def get_edt_time() -> dict:
    """
    获取当前美东时间 + 交易时段。

    返回:
        {
            "edt_datetime": "2026-05-05 12:31 PM EDT",
            "edt_iso": "2026-05-05T12:31:00-04:00",
            "day_of_week": "Tuesday",
            "session": "REGULAR",
            "session_label": "盘中 (Regular Trading Hours)",
            "timezone": "EDT (UTC-4)",
            "source": "time.is"
        }
    """
    errors = []
    edt_str = None
    day_str = None

    # 方案 A: time.is 解析
    try:
        resp = requests.get(TIME_IS_URL, timeout=REQUEST_TIMEOUT, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # time.is 首页大时间: <time id="clock">12:31:52PM</time>
        clock_el = soup.find("time", id="clock")
        if clock_el:
            time_str = clock_el.get_text(strip=True)  # e.g. "12:31:52PM"

            # 日期: 通常在 <div id="dd"> 或附近
            # 结构为: <div id="dd">Date: Thursday, May 5, 2026</div> 或类似
            dd_el = soup.find("div", id="dd")
            date_str = None
            if dd_el:
                date_text = dd_el.get_text(strip=True).replace("Date:", "").strip()
                date_str = date_text  # e.g. "Thursday, May 5, 2026"

            edt_str = f"{date_str} {time_str} EDT" if date_str else f"{time_str} EDT"

            # 提取星期几
            if date_str:
                day_match = re.match(r"(\w+)", date_str)
                if day_match:
                    day_str = day_match.group(1)
    except Exception as exc:
        errors.append(f"time.is parse failed: {exc}")

    # 方案 B: 回退 — 用 UTC 时间 + 时区换算
    if not edt_str:
        try:
            now_utc = datetime.utcnow()
            from datetime import timedelta, timezone as tz
            # EDT = UTC-4
            edt_offset = timedelta(hours=-4)
            edt_now = now_utc + edt_offset
            edt_str = edt_now.strftime("%Y-%m-%d %I:%M:%S %p EDT (computed)")
            day_str = edt_now.strftime("%A")
            errors.append("time.is 解析失败，使用 UTC-4 换算")
        except Exception as exc:
            errors.append(f"fallback time compute failed: {exc}")

    # ---- 解析时间判断交易时段 -------------------------------------------
    session = "UNKNOWN"
    session_label = "未知"
    iso_time = None

    if edt_str:
        hour = _extract_hour(edt_str)
        minute = _extract_minute(edt_str)
        if hour is not None:
            total_min = hour * 60 + minute

            if total_min < 240:              # < 4:00 AM
                session = "CLOSED"
                session_label = "已收盘 (盘后/凌晨)"
            elif total_min < 570:             # 4:00 - 9:30 AM
                session = "PRE"
                session_label = "盘前 (Premarket)"
            elif total_min < 960:             # 9:30 AM - 4:00 PM
                session = "REGULAR"
                session_label = "盘中 (Regular Trading Hours)"
            elif total_min < 1200:            # 4:00 - 8:00 PM
                session = "POST"
                session_label = "盘后 (After Hours)"
            else:                             # > 8:00 PM
                session = "CLOSED"
                session_label = "已收盘"

            # 简单 ISO
            try:
                iso_time = _to_iso(edt_str)
            except Exception:
                pass

    return {
        "edt_datetime": edt_str,
        "edt_iso": iso_time,
        "day_of_week": day_str,
        "session": session,
        "session_label": session_label,
        "timezone": "EDT (UTC-4)",
        "source": "time.is + fallback UTC-4 compute",
        "errors": errors,
    }


def _extract_hour(text: str) -> int | None:
    """从 "12:31:52PM" / "12:31 PM" 提取24h制小时。"""
    m = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM|am|pm)", text)
    if not m:
        m = re.search(r"(\d{1,2}):(\d{2})", text)
        if m:
            return int(m.group(1))
        return None
    h = int(m.group(1))
    ampm = m.group(4).upper() if m.lastindex >= 4 else ""
    if ampm == "PM" and h != 12:
        h += 12
    elif ampm == "AM" and h == 12:
        h = 0
    return h


def _extract_minute(text: str) -> int:
    m = re.search(r"(\d{1,2}):(\d{2})", text)
    return int(m.group(2)) if m else 0


def _to_iso(text: str) -> str:
    """尝试转 ISO 8601。"""
    # 解析日期: "Thursday, May 5, 2026" 或 "May 5, 2026"
    date_match = re.search(
        r"(\w+day)?,?\s*(\w+)\s+(\d{1,2}),?\s+(\d{4})", text
    )
    h = _extract_hour(text)
    m = _extract_minute(text)

    if date_match and h is not None:
        month_name = date_match.group(2).lower()
        month = _MONTHS.get(month_name, 1)
        day = int(date_match.group(3))
        year = int(date_match.group(4))
        return f"{year:04d}-{month:02d}-{day:02d}T{h:02d}:{m:02d}:00-04:00"
    return text
