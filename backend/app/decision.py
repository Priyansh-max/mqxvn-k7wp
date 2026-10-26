"""Day-ahead decision window: which forecast a trader would have had at gate close."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from .config import settings

LONDON = ZoneInfo("Europe/London")
CET = ZoneInfo("Europe/Berlin")  # CET/CEST — EPEX gate is quoted in CET


def gate_close_utc(delivery_day: date) -> datetime:
    """
    EPEX SPOT GB day-ahead auction gate closes at 09:20 CET on D-1
    for delivery day D (00:00–24:00 Europe/London settlement day).

    09:20 CET = 08:20 UTC (CET is UTC+1; CEST would be 07:20 UTC — we use
    Europe/Berlin so DST is handled correctly).
    """
    d_minus_1 = delivery_day - timedelta(days=1)
    local_gate = datetime(
        d_minus_1.year,
        d_minus_1.month,
        d_minus_1.day,
        9,
        20,
        tzinfo=CET,
    )
    return local_gate.astimezone(timezone.utc)


def parse_ts(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def delivery_day_bounds_utc(delivery_day: date) -> tuple[datetime, datetime]:
    """Settlement day D in Europe/London → [start, end) in UTC."""
    start_local = datetime.combine(delivery_day, time(0, 0), tzinfo=LONDON)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def select_decision_forecast(
    forecasts: list[dict[str, Any]],
    delivery_day: date,
) -> tuple[str | None, list[dict[str, Any]]]:
    """
    Decision rule
    -------------
    For delivery day D, keep only WINDFOR rows whose publishTime is <=
    gate_close on D-1 (09:20 CET). Among those, take the latest publishTime
    (the freshest run a trader could still use before bidding). Return the
    half-hourly points for that run whose startTime falls on delivery day D
    (London calendar day).
    """
    gate = gate_close_utc(delivery_day)
    day_start, day_end = delivery_day_bounds_utc(delivery_day)

    eligible = [r for r in forecasts if parse_ts(r["publishTime"]) <= gate]
    if not eligible:
        return None, []

    # Group by publishTime; pick latest
    by_pub: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in eligible:
        by_pub[r["publishTime"]].append(r)
    latest_pub = max(by_pub.keys(), key=lambda p: parse_ts(p))
    series = [
        r
        for r in by_pub[latest_pub]
        if day_start <= parse_ts(r["startTime"]) < day_end
    ]
    series.sort(key=lambda r: r["startTime"])
    return latest_pub, series


def january_delivery_days() -> list[date]:
    y, m = map(int, settings.delivery_month.split("-"))
    d = date(y, m, 1)
    days: list[date] = []
    while d.month == m:
        days.append(d)
        d += timedelta(days=1)
    return days


def build_paired_series(
    actuals: list[dict[str, Any]],
    forecasts: list[dict[str, Any]],
    delivery_days: list[date] | None = None,
) -> list[dict[str, Any]]:
    """Pair decision-relevant forecast vs actual for each half-hour."""
    days = delivery_days or january_delivery_days()
    actual_by_start = {a["startTime"]: float(a["generation"]) for a in actuals}

    paired: list[dict[str, Any]] = []
    for day in days:
        pub, series = select_decision_forecast(forecasts, day)
        gate = gate_close_utc(day)
        for row in series:
            st = row["startTime"]
            fc = float(row["generation"])
            act = actual_by_start.get(st)
            lead_hours = (parse_ts(st) - gate).total_seconds() / 3600.0
            hour_local = parse_ts(st).astimezone(LONDON).hour
            paired.append(
                {
                    "deliveryDay": day.isoformat(),
                    "startTime": st,
                    "publishTime": pub,
                    "gateCloseUtc": gate.isoformat().replace("+00:00", "Z"),
                    "forecastMw": fc,
                    "actualMw": act,
                    "errorMw": (fc - act) if act is not None else None,
                    "leadHours": round(lead_hours, 2),
                    "hourLocal": hour_local,
                }
            )
    return paired
