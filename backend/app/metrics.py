"""Forecast accuracy metrics and residual procurement band."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np


def _errors(paired: list[dict[str, Any]]) -> np.ndarray:
    errs = [p["errorMw"] for p in paired if p.get("errorMw") is not None]
    return np.asarray(errs, dtype=float)


def summarise(paired: list[dict[str, Any]]) -> dict[str, Any]:
    errs = _errors(paired)
    if errs.size == 0:
        return {
            "n": 0,
            "maeMw": None,
            "rmseMw": None,
            "mapePct": None,
            "biasMw": None,
            "p10AbsErrorMw": None,
            "p50AbsErrorMw": None,
            "p90AbsErrorMw": None,
            "residualBandMw": None,
            "note": "No paired actuals yet for this window.",
        }

    abs_e = np.abs(errs)
    actuals = np.asarray(
        [p["actualMw"] for p in paired if p.get("errorMw") is not None], dtype=float
    )
    # MAPE: skip near-zero actuals to avoid blow-ups
    mask = actuals > 100.0
    mape = (
        float(np.mean(np.abs(errs[mask] / actuals[mask])) * 100.0)
        if mask.any()
        else None
    )

    mae = float(np.mean(abs_e))
    # Actionable residual band: cover ~90% of absolute errors (P90)
    p90 = float(np.percentile(abs_e, 90))

    return {
        "n": int(errs.size),
        "maeMw": round(mae, 1),
        "rmseMw": round(float(np.sqrt(np.mean(errs**2))), 1),
        "mapePct": round(mape, 2) if mape is not None else None,
        "biasMw": round(float(np.mean(errs)), 1),
        "p10AbsErrorMw": round(float(np.percentile(abs_e, 10)), 1),
        "p50AbsErrorMw": round(float(np.percentile(abs_e, 50)), 1),
        "p90AbsErrorMw": round(p90, 1),
        "residualBandMw": round(p90, 1),
        "interpretation": (
            f"Size thermal/residual cover about ±{round(p90)} MW around the "
            f"decision-window wind forecast to cover ~90% of Jan-2026 paired intervals."
        ),
    }


def by_lead_hour(paired: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[int, list[float]] = defaultdict(list)
    for p in paired:
        if p.get("errorMw") is None:
            continue
        lead = int(round(p["leadHours"]))
        buckets[lead].append(abs(p["errorMw"]))

    out = []
    for lead in sorted(buckets):
        arr = np.asarray(buckets[lead], dtype=float)
        out.append(
            {
                "leadHours": lead,
                "n": int(arr.size),
                "maeMw": round(float(np.mean(arr)), 1),
                "p90Mw": round(float(np.percentile(arr, 90)), 1),
            }
        )
    return out


def by_hour_of_day(paired: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[int, list[float]] = defaultdict(list)
    for p in paired:
        if p.get("errorMw") is None:
            continue
        buckets[int(p["hourLocal"])].append(abs(p["errorMw"]))

    out = []
    for hour in range(24):
        arr = buckets.get(hour)
        if not arr:
            continue
        a = np.asarray(arr, dtype=float)
        out.append(
            {
                "hourLocal": hour,
                "n": int(a.size),
                "maeMw": round(float(np.mean(a)), 1),
                "p90Mw": round(float(np.percentile(a, 90)), 1),
            }
        )
    return out


def error_histogram(paired: list[dict[str, Any]], bins: int = 24) -> dict[str, Any]:
    errs = _errors(paired)
    if errs.size == 0:
        return {"bins": [], "counts": []}
    counts, edges = np.histogram(errs, bins=bins)
    centers = ((edges[:-1] + edges[1:]) / 2).tolist()
    return {
        "binCentersMw": [round(c, 1) for c in centers],
        "counts": [int(c) for c in counts.tolist()],
        "binEdgesMw": [round(float(e), 1) for e in edges.tolist()],
    }
