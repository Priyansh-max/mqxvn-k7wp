"""Elexon BMRS Insights stream client (FUELHH + WINDFOR)."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import settings

log = logging.getLogger(__name__)


def _headers() -> dict[str, str]:
    h = {"Accept": "application/json"}
    if settings.elexon_api_key:
        h["Authorization"] = f"Bearer {settings.elexon_api_key}"
    return h


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _get(path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    url = f"{settings.elexon_base_url.rstrip('/')}/{path.lstrip('/')}"
    with httpx.Client(timeout=120.0, headers=_headers()) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        if isinstance(data, list):
            return data
        return []


def _cache_path(name: str) -> Path:
    return settings.cache_dir / name


def _load_cache(name: str) -> list[dict[str, Any]] | None:
    p = _cache_path(name)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return None


def _save_cache(name: str, rows: list[dict[str, Any]]) -> None:
    p = _cache_path(name)
    p.write_text(json.dumps(rows), encoding="utf-8")


def fetch_wind_actuals(
    settlement_from: date,
    settlement_to: date,
    *,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    """Half-hourly WIND outturn from FUELHH stream."""
    cache_name = f"fuelhh_wind_{settlement_from.isoformat()}_{settlement_to.isoformat()}.json"
    if use_cache:
        cached = _load_cache(cache_name)
        if cached is not None:
            return cached

    rows = _get(
        "/datasets/FUELHH/stream",
        {
            "settlementDateFrom": settlement_from.isoformat(),
            "settlementDateTo": settlement_to.isoformat(),
            "fuelType": "WIND",
        },
    )
    # Deduplicate by startTime (keep latest publish)
    by_start: dict[str, dict[str, Any]] = {}
    for row in rows:
        st = row.get("startTime")
        if not st:
            continue
        prev = by_start.get(st)
        if prev is None or str(row.get("publishTime", "")) >= str(prev.get("publishTime", "")):
            by_start[st] = row
    out = sorted(by_start.values(), key=lambda r: r["startTime"])
    _save_cache(cache_name, out)
    return out


def fetch_wind_forecasts(
    publish_from: datetime,
    publish_to: datetime,
    *,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    """WINDFOR stream rows published in [publish_from, publish_to]."""
    cache_name = (
        f"windfor_{publish_from.strftime('%Y%m%dT%H%M')}_{publish_to.strftime('%Y%m%dT%H%M')}.json"
    )
    if use_cache:
        cached = _load_cache(cache_name)
        if cached is not None:
            return cached

    rows = _get(
        "/datasets/WINDFOR/stream",
        {
            "publishDateTimeFrom": publish_from.astimezone(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "publishDateTimeTo": publish_to.astimezone(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        },
    )
    _save_cache(cache_name, rows)
    return rows


def fetch_january_2026_bundle(*, use_cache: bool = True) -> dict[str, Any]:
    """
    Pull actuals for Jan 2026 and forecast publications covering the
    day-ahead decision windows (D-1 mornings from 2025-12-31 through 2026-01-31).
    """
    cache_name = "jan2026_bundle.json"
    if use_cache:
        cached = _load_cache(cache_name)
        if cached is not None:
            return cached

    actuals = fetch_wind_actuals(date(2026, 1, 1), date(2026, 1, 31), use_cache=use_cache)

    # Chunk publish windows to keep responses manageable (~1 day each)
    pubs: list[dict[str, Any]] = []
    start = datetime(2025, 12, 30, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 31, 12, 0, tzinfo=timezone.utc)
    cursor = start
    while cursor < end:
        nxt = min(cursor + timedelta(days=1), end)
        chunk = fetch_wind_forecasts(cursor, nxt, use_cache=use_cache)
        pubs.extend(chunk)
        cursor = nxt
        log.info("WINDFOR chunk %s → %s: %s rows", cursor, nxt, len(chunk))

    bundle = {
        "actuals": actuals,
        "forecasts": pubs,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_cache(cache_name, [bundle])  # wrap for list cache helper consistency
    # Also write direct object cache
    _cache_path(cache_name).write_text(json.dumps(bundle), encoding="utf-8")
    return bundle


def load_bundle() -> dict[str, Any]:
    p = _cache_path("jan2026_bundle.json")
    if p.exists():
        raw = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "actuals" in raw[0]:
            return raw[0]
        if isinstance(raw, dict) and "actuals" in raw:
            return raw
    return fetch_january_2026_bundle(use_cache=True)
