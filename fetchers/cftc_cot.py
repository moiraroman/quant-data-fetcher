"""
CFTC Commitments of Traders (COT) Fetcher
=========================================
从 CFTC 官网抓取每周持仓报告数据。
URL: cftc.gov/dea/futures/
数据: Asset Manager / Leveraged Fund / Dealer 持仓
格式: CSV (压缩包或文本)
"""

import csv
import io
import logging
import re
import zipfile
from datetime import datetime
from typing import Optional

import requests

logger = logging.getLogger("cftc_cot_fetcher")

CFTC_CSV_URL = (
    "https://www.cftc.gov/files/dea/history/"
    "com_disagg_txt_2026.zip"
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/132.0.0.0 Safari/537.36"
    ),
}
TIMEOUT = 30

# CFTC 商品代码 → 名称映射
COT_MAP = {
    "138741": "E-MINI S&P 500",
    "209742": "E-MINI NASDAQ 100",
    "1170E1": "VIX FUTURES",
    "042602": "US 10Y NOTE",
    "043602": "US 30Y BOND",
    "044601": "US 2Y NOTE",
}


def get_cot_report(commodity_code: str = "138741") -> Optional[dict]:
    """
    获取特定商品的最新 COT 持仓数据。

    返回:
    {
      comm_name, as_of_date,
      asset_mgr: { long, short, net },
      leveraged_fund: { long, short, net },
      dealer: { long, short, net },
      total_oi
    }
    """
    try:
        resp = requests.get(CFTC_CSV_URL, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception as exc:
        logger.error("CFTC COT download error: %s", exc)
        return None

    # 解压并读CSV (disaggregated格式)
    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            # 找主数据文件
            csv_files = [n for n in zf.namelist() if n.lower().endswith(".txt")
                         and "disagg" in n.lower()]
            if not csv_files:
                csv_files = [n for n in zf.namelist() if n.lower().endswith(".txt")]
            if not csv_files:
                logger.error("CFTC: 找不到数据文件")
                return None

            with zf.open(csv_files[0]) as f:
                content = io.TextIOWrapper(f, encoding="utf-8-sig")
                reader = csv.reader(content)

                for row in reader:
                    if len(row) < 10:
                        continue
                    # Disaggregated Futures: 第一列为日期 YYYY-MM-DD
                    commodity = row[1].strip() if len(row) > 1 else ""

                    if commodity == commodity_code:
                        row = [c.strip() for c in row]
                        record = _parse_disagg_row(row)
                        if record:
                            record["source"] = "CFTC COT"
                            record["fetched_at"] = datetime.now().isoformat()
                            logger.info(
                                "CFTC [%s]: Date=%s AM=%.0f LF=%.0f DL=%.0f",
                                record.get("comm_name", commodity_code),
                                record.get("as_of_date", "?"),
                                record.get("asset_mgr", {}).get("net", 0),
                                record.get("leveraged_fund", {}).get("net", 0),
                                record.get("dealer", {}).get("net", 0),
                            )
                            return record

            logger.warning("CFTC: 未找到 code=%s", commodity_code)
            return None

    except Exception as exc:
        logger.error("CFTC parse error: %s", exc)
        return None


def get_cot_all() -> dict:
    """
    一次获取所有关注标的的 COT 报告。
    返回: { code: { ... }, ... }
    """
    results = {}
    for code in COT_MAP.keys():
        data = get_cot_report(code)
        if data:
            results[code] = data
    return results


def _parse_disagg_row(row: list) -> Optional[dict]:
    """
    Parse Disaggregated Futures COT row.

    Disaggregated格式:
      0: Market_and_Exchange_Names
      1: As_of_Date_in_Form_YYMMDD
      2: CFTC_Contract_Market_Code
      3: CFTC_Market_Code
      4: CFTC_Region_Code
      5: CFTC_Commodity_Code
      ...
    But actual format:
      0: as_of_date (YYYY-MM-DD)
      1: commodity_code (e.g. "138741")
      2: comm_name
      3-4: Producer/Merchant Long/Short
      5-6: Managed Money Long/Short (= Leveraged Fund equiv)
      ...
    Actually the CFTC format varies. Let me try to read it properly.

    Disaggregated Futures COT Format:
      0: Market_and_Exchange_Names
      1: Report_Date_as_YYYY-MM-DD
      ... (many columns)
    """
    as_of_idx = 0

    # 找日期列
    report_date = None
    for i, val in enumerate(row):
        if re.match(r"^\d{4}-\d{1,2}-\d{1,2}$", val):
            report_date = val
            as_of_idx = i
            break

    if report_date is None:
        return None

    name = COT_MAP.get(row[as_of_idx + 1] if as_of_idx + 1 < len(row) else "", "")

    # 列映射 (Disaggregated Report)
    # Producer/Merchant  → row[4-5]
    # Managed Money      → row[6-7]  (Leveraged Fund proxy)
    # Swap Dealer        → row[11-12] (Dealer proxy)
    # Other Reportables  → row[13-14]
    # Nonreportable      → row[15-16]

    try:
        # Managed Money (=Leveraged Fund in Disagg)
        mm_long = int(row[6]) if len(row) > 6 else 0
        mm_short = int(row[7]) if len(row) > 7 else 0

        # Dealer (Swap Dealer), use as proxy
        dl_long = int(row[11]) if len(row) > 11 else 0
        dl_short = int(row[12]) if len(row) > 12 else 0

        # Other (includes traditional Asset Managers)
        other_long = int(row[13]) if len(row) > 13 else 0
        other_short = int(row[14]) if len(row) > 14 else 0

        # 假定 Asset Manager = MM + Other的某部分
        # (CFTC 不单独报告Asset Manager在Disagg格式中)
        am_long = other_long
        am_short = other_short

        # Total OI
        total_oi = mm_long + mm_short + dl_long + dl_short + am_long + am_short

    except (ValueError, IndexError):
        return None

    return {
        "comm_code": row[as_of_idx + 1] if as_of_idx + 1 < len(row) else "",
        "comm_name": name,
        "as_of_date": report_date,
        "asset_manager": {
            "long": am_long,
            "short": am_short,
            "net": am_long - am_short,
        },
        "leveraged_fund": {
            "long": mm_long,
            "short": mm_short,
            "net": mm_long - mm_short,
        },
        "dealer": {
            "long": dl_long,
            "short": dl_short,
            "net": dl_long - dl_short,
        },
        "total_oi": total_oi,
    }