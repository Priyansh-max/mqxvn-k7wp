"""Boreas FastAPI application."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from . import elexon
from .config import settings
from .decision import (
    build_paired_series,
    gate_close_utc,
    january_delivery_days,
    select_decision_forecast,
)
from .metrics import by_hour_of_day, by_lead_hour, error_histogram, summarise

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("boreas")

app = FastAPI(
    title="Boreas",
    description="Day-ahead GB wind forecast intelligence for January 2026",
    version="1.0.0",
    default_response_class=ORJSONResponse,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_STATE: dict[str, Any] = {"bundle": None, "paired": None}


def _ensure_data() -> dict[str, Any]:
    if _STATE["bundle"] is None:
        log.info("Loading January 2026 Elexon bundle…")
        _STATE["bundle"] = elexon.load_bundle()
        _STATE["paired"] = build_paired_series(
            _STATE["bundle"]["actuals"], _STATE["bundle"]["forecasts"]
        )
        log.info(
            "Loaded %s actuals, %s forecast rows, %s paired points",
            len(_STATE["bundle"]["actuals"]),
            len(_STATE["bundle"]["forecasts"]),
            len(_STATE["paired"]),
        )
    return _STATE


@app.on_event("startup")
def startup() -> None:
    try:
        _ensure_data()
    except Exception as exc:  # noqa: BLE001 — surface later via /health
        log.exception("Startup data load failed: %s", exc)
        _STATE["error"] = str(exc)


@app.get("/api/health")
def health() -> dict[str, Any]:
    ok = _STATE.get("bundle") is not None
    return {
        "status": "ok" if ok else "degraded",
        "product": "Boreas",
        "deliveryMonth": settings.delivery_month,
        "error": _STATE.get("error"),
        "actuals": len(_STATE["bundle"]["actuals"]) if ok else 0,
        "forecastRows": len(_STATE["bundle"]["forecasts"]) if ok else 0,
        "paired": len(_STATE["paired"]) if ok else 0,
    }


@app.get("/api/methodology")
def methodology() -> dict[str, Any]:
    sample = date(2026, 1, 15)
    gate = gate_close_utc(sample)
    return {
        "product": "Boreas",
        "scope": "National GB wind actuals (FUELHH/WIND) + forecasts (WINDFOR) via Elexon Insights stream APIs. January 2026 delivery days only.",
        "decisionRule": {
            "summary": (
                "For delivery day D, use the latest WINDFOR publication with "
                "publishTime ≤ EPEX SPOT GB day-ahead gate close on D-1 "
                "(09:20 CET). Retain half-hours whose startTime falls on D "
                "in Europe/London."
            ),
            "gateCloseCet": "09:20",
            "exampleDeliveryDay": sample.isoformat(),
            "exampleGateCloseUtc": gate.isoformat().replace("+00:00", "Z"),
        },
        "sources": {
            "actuals": "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream",
            "forecasts": "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream",
            "auth": "Public Insights API — no key required. Optional ELEXON_API_KEY env if a gateway is introduced later.",
        },
        "metrics": [
            "MAE",
            "RMSE",
            "MAPE (actuals > 100 MW)",
            "Bias (mean signed error)",
            "P90 absolute error → residual procurement band",
        ],
    }


@app.post("/api/refresh")
def refresh(force: bool = False) -> dict[str, Any]:
    _STATE["bundle"] = elexon.fetch_january_2026_bundle(use_cache=not force)
    _STATE["paired"] = build_paired_series(
        _STATE["bundle"]["actuals"], _STATE["bundle"]["forecasts"]
    )
    _STATE.pop("error", None)
    return health()


@app.get("/api/days")
def list_days() -> dict[str, Any]:
    _ensure_data()
    paired = _STATE["paired"]
    by_day: dict[str, dict[str, Any]] = {}
    for p in paired:
        d = p["deliveryDay"]
        slot = by_day.setdefault(
            d,
            {
                "deliveryDay": d,
                "publishTime": p["publishTime"],
                "gateCloseUtc": p["gateCloseUtc"],
                "points": 0,
                "withActual": 0,
            },
        )
        slot["points"] += 1
        if p["actualMw"] is not None:
            slot["withActual"] += 1
    days = sorted(by_day.values(), key=lambda x: x["deliveryDay"])
    return {"days": days, "count": len(days)}


@app.get("/api/series")
def series(
    day: str | None = Query(None, description="YYYY-MM-DD delivery day"),
) -> dict[str, Any]:
    _ensure_data()
    paired = _STATE["paired"]
    if day:
        try:
            date.fromisoformat(day)
        except ValueError as exc:
            raise HTTPException(400, "day must be YYYY-MM-DD") from exc
        paired = [p for p in paired if p["deliveryDay"] == day]
        if not paired:
            raise HTTPException(404, f"No decision-window series for {day}")
    return {"points": paired, "count": len(paired)}


@app.get("/api/day/{day}")
def day_detail(day: str) -> dict[str, Any]:
    _ensure_data()
    try:
        d = date.fromisoformat(day)
    except ValueError as exc:
        raise HTTPException(400, "Invalid date") from exc

    pub, fc = select_decision_forecast(_STATE["bundle"]["forecasts"], d)
    points = [p for p in _STATE["paired"] if p["deliveryDay"] == day]
    return {
        "deliveryDay": day,
        "publishTime": pub,
        "gateCloseUtc": gate_close_utc(d).isoformat().replace("+00:00", "Z"),
        "forecastPoints": len(fc),
        "metrics": summarise(points),
        "points": points,
    }


@app.get("/api/metrics")
def metrics(
    day: str | None = Query(None),
) -> dict[str, Any]:
    _ensure_data()
    paired = _STATE["paired"]
    if day:
        paired = [p for p in paired if p["deliveryDay"] == day]
    return {
        "overall": summarise(paired),
        "byLeadHour": by_lead_hour(paired),
        "byHourLocal": by_hour_of_day(paired),
        "errorHistogram": error_histogram(paired),
        "deliveryDays": [d.isoformat() for d in january_delivery_days()],
        "filterDay": day,
    }


@app.get("/api/overview")
def overview() -> dict[str, Any]:
    """Narrative payload for the trader landing experience."""
    _ensure_data()
    paired = _STATE["paired"]
    overall = summarise(paired)
    # Latest delivery day with any actuals
    days_with = sorted(
        {p["deliveryDay"] for p in paired if p["actualMw"] is not None}
    )
    latest = days_with[-1] if days_with else None
    latest_points = [p for p in paired if p["deliveryDay"] == latest] if latest else []
    return {
        "product": "Boreas",
        "tagline": "Know the wind before the gate.",
        "deliveryMonth": settings.delivery_month,
        "overall": overall,
        "latestDeliveryDay": latest,
        "latestDayMetrics": summarise(latest_points) if latest else None,
        "dayCount": len({p["deliveryDay"] for p in paired}),
        "pairedHalfHours": len([p for p in paired if p["actualMw"] is not None]),
    }
