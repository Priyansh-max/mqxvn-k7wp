# Boreas

Day-ahead **GB national wind** desk for January 2026 purchase decisions.

Built for a UK utility buying in the wholesale day-ahead market: show the wind forecast a trader would actually have had before the gate, then quantify error so residual / thermal cover can be sized.

**Live deploy:** _(pending Vercel login — see [SUBMISSION.md](SUBMISSION.md) morning steps)_  
**GitHub:** https://github.com/Priyansh-max/mqxvn-k7wp  
**Local demo:** `docker compose up --build` → http://localhost:8080

---

## Directory map

```
mqxvn-k7wp/
├── backend/                 Python FastAPI
│   ├── app/
│   │   ├── main.py          HTTP API
│   │   ├── elexon.py        FUELHH + WINDFOR client + cache
│   │   ├── decision.py      Day-ahead gate / publishTime rule
│   │   └── metrics.py       MAE, RMSE, MAPE, bias, P90 band
│   ├── scripts/ingest.py    Prefetch Jan 2026 into data/cache
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                React + Vite + Recharts
│   ├── src/App.tsx          Trader narrative UI
│   └── Dockerfile           nginx + /api proxy
├── api/index.py             Vercel serverless (Mangum → FastAPI)
├── data/cache/              Baked jan2026_bundle.json
├── docs/                    Architecture + assignment brief (md/pdf)
├── media/                   Silent demo MP4
├── docker-compose.yml
├── SPEAKER_SCRIPT.md
└── SUBMISSION.md
```

## Quick start

### Docker (recommended)

```bash
docker compose up --build
```

- App: http://localhost:8080  
- API: http://localhost:8000/api/health  

### Local (dev)

```bash
# API
python -m venv .venv
# Windows: .\.venv\Scripts\activate
pip install -r backend/requirements.txt
set CACHE_DIR=%CD%\data\cache   # or export CACHE_DIR=...
uvicorn app.main:app --reload --app-dir backend --port 8000

# UI
cd frontend && npm install && npm run dev
```

UI: http://localhost:5173 (proxies `/api` → `:8000`).

Refresh live Elexon data (optional):

```bash
python backend/scripts/ingest.py
curl -X POST "http://127.0.0.1:8000/api/refresh?force=true"
```

## Decision-window methodology

**Rule.** For delivery day `D` (00:00–24:00 Europe/London):

1. Day-ahead gate = **09:20 CET on D−1** (EPEX SPOT GB).
2. Keep WINDFOR rows with `publishTime ≤` that gate.
3. Take the **latest** such publication.
4. Keep half-hours / hours with `startTime` on day `D`.
5. Pair to FUELHH `fuelType=WIND` on equal `startTime`.

WINDFOR is hourly; FUELHH is half-hourly → accuracy sample is **hourly** (744 paired intervals in Jan 2026).

**Residual band** = P90 of absolute forecast error — a practical MW cover around the point forecast.

Full write-up: [docs/architecture-and-tradeoffs.md](docs/architecture-and-tradeoffs.md).

## Elexon data notes

| Dataset | Endpoint | Use |
| --- | --- | --- |
| Actuals | `GET /datasets/FUELHH/stream?fuelType=WIND` | National half-hour wind outturn |
| Forecasts | `GET /datasets/WINDFOR/stream` | Wind generation forecast runs |

Base URL: `https://data.elexon.co.uk/bmrs/api/v1`  
Auth: **none** — Insights API is public (rate limit ~5k req/min). Optional env `ELEXON_API_KEY` if you later front a keyed gateway.  
Docs: https://bmrs.elexon.co.uk/api-documentation/

January 2026 actuals and forecast publications were verified live. A baked `data/cache/jan2026_bundle.json` ships for offline Docker/Vercel cold starts.

## Accuracy outputs

- MAE, RMSE, MAPE (actuals > 100 MW), signed bias  
- Error vs lead time from gate  
- Signed-error histogram  
- **Residual procurement band (P90 \|error\|)**

## AI assistance

This take-home was built with **AI coding assistance** (Cursor / Composer agent) for scaffolding, API client, UI, docs, and Docker. Human direction set product narrative, decision rule, and acceptance criteria. All Elexon numbers are from live API responses / the cached Jan 2026 bundle — not model-invented MW.

## Docs & demo

| Artifact | Path |
| --- | --- |
| Architecture PDF | `docs/architecture-and-tradeoffs.pdf` |
| Assignment brief PDF | `docs/assignment-brief-and-deliverables.pdf` |
| Silent demo | `media/boreas-demo-silent.mp4` |
| Narration script | `SPEAKER_SCRIPT.md` |
| Form paste sheet | `SUBMISSION.md` |

## License

Interview take-home sample — not for production trading.
