# Boreas — Architecture, Design & Tradeoffs

## Product

**Boreas** is a day-ahead wind desk for a UK energy utility. It answers two questions for January 2026 delivery:

1. What national wind forecast would a trader have had **before** the day-ahead gate?
2. How accurate is that decision-window forecast vs Elexon outturn, and what **residual band** should size thermal cover?

## Architecture

```
┌─────────────┐     /api/*      ┌──────────────────┐     HTTPS      ┌─────────────────────┐
│  React SPA  │ ──────────────► │  FastAPI (Boreas) │ ─────────────► │ Elexon Insights API │
│  Vite/TS    │                 │  decision+metrics │   (cached)     │ FUELHH + WINDFOR    │
└─────────────┘                 └──────────────────┘                 └─────────────────────┘
       │                                  │
       │ docker: nginx proxy              │ data/cache/jan2026_bundle.json
       ▼                                  ▼
┌──────────────────────────────────────────────────┐
│              docker compose (local)               │
│   web (:8080)  →  api (:8000)  →  volume cache    │
└──────────────────────────────────────────────────┘
```

Deploy target: **Vercel** (static SPA + Python serverless `api/index.py` via Mangum). Local path of record: `docker compose up --build`.

## Components

| Layer | Choice | Role |
| --- | --- | --- |
| Frontend | React + Vite + Recharts | Narrative trader UI, day picker, forecast vs actual, error charts |
| Backend | FastAPI + NumPy | Elexon client, decision window, MAE/RMSE/MAPE/bias/P90 band |
| Cache | JSON bundle | Offline/demo speed; avoid re-hitting Elexon on every boot |
| Packaging | Docker Compose | One-command local repro |
| Hosting | Vercel | FE + serverless API when credentials available |

## Decision-window rule

For delivery day **D** (00:00–24:00 `Europe/London`):

1. Gate close = **09:20 CET on D−1** (EPEX SPOT GB day-ahead).
2. Eligible forecasts: WINDFOR rows with `publishTime ≤ gate`.
3. Select the **latest** eligible `publishTime`.
4. Keep points whose `startTime` falls on D.
5. Pair to FUELHH `fuelType=WIND` on matching `startTime`.

WINDFOR publishes on the hour; FUELHH is half-hourly → paired sample is **hourly** (744 points across Jan 2026).

## Tradeoffs

| Decision | Alternative | Why we chose this |
| --- | --- | --- |
| Stream dataset APIs | Opinionated `/forecast/generation/wind/*` | Assignment specifies FUELHH/WINDFOR stream; publish-time filtering needs dataset history |
| Bake Jan 2026 cache | Live-only fetch | Cold start + rate limits; deterministic demo; refresh via `POST /api/refresh?force=true` |
| P90 abs error as band | ±1.96·σ or MAE×k | Non-parametric, actionable for procurement; robust to skewed error |
| Hourly pairing | Aggregate HH to hour | Exact timestamp join; no invented aggregation policy |
| Single-month scope | Full history backtest | Matches purchase-decision window in the brief |
| Vercel-only deploy | Heroku/Fly | Explicit constraint; Docker remains the guaranteed path |
| Mangum on Vercel | Long-running container | Fits Vercel; lifespan off + precomputed cache |

## Security & ops

- Elexon Insights is **public** (no key). Optional `ELEXON_API_KEY` documented for future gateways.
- CORS configurable via `CORS_ORIGINS`.
- No PII; national aggregates only.

## Testing posture

- Live Elexon ingest verified for Jan 2026.
- `/api/health`, `/api/overview`, `/api/series?day=` smoke-tested locally.
- `docker compose` is the integration smoke path.
