# Boreas — Speaker Script (≤10 minutes)

Silent walkthrough MP4: `media/boreas-demo-silent.mp4`  
Use this script when recording the narrated unlisted YouTube in the morning.

---

## Part 1 — Client pitch (~4–5 min)

**[0:00–0:30] Hook**  
“You’re buying GB power day-ahead. Wind is the biggest flexible renewable on the stack — but the forecast you see at 11am is not the one you had when the gate closed. Boreas shows only what a trader could actually use.”

**[0:30–1:30] Product**  
Open the hero: brand **Boreas**, headline *Day-ahead wind you can buy against.*  
“One composition: national wind for January 2026, decision-window forecasts vs outturn, and a residual band for thermal cover.”

**[1:30–3:00] Desk**  
Scroll to the desk. Select a delivery day (e.g. 15 Jan).  
“Dashed amber is the gate-time forecast. Solid teal is FUELHH wind actual. We lock publish time to ≤ 09:20 CET on D−1 — EPEX day-ahead gate.”

Point at MAE / RMSE / bias / MAPE strip.  
“These are not vanity metrics — they feed the residual band.”

**[3:00–4:30] Actionable number**  
Highlight **Residual band ±X MW**.  
“We use the 90th percentile of absolute error. If you’re sizing residual or thermal against this wind shape, cover about that band around the point forecast to clear most half-hour misses in January.”

**[4:30–5:00] Close pitch**  
“Same data you already trust — Elexon — filtered like a trader, not like a backtest with look-ahead.”

---

## Part 2 — Tech lead KT (~4–5 min)

**[5:00–6:00] Architecture**  
Show `docs/architecture-and-tradeoffs.md` diagram (or README map).  
“React SPA → FastAPI → Elexon Insights stream. Docker Compose for local. Vercel target: static FE + Mangum-wrapped API. Jan 2026 bundle baked for cold start.”

**[6:00–7:00] Decision engine**  
Open `backend/app/decision.py`.  
“`gate_close_utc(D)` uses 09:20 Europe/Berlin on D−1. Latest eligible WINDFOR publish. Pair on `startTime`. WINDFOR hourly × FUELHH HH → 744 paired intervals.”

**[7:00–8:00] Metrics**  
Open `backend/app/metrics.py` and the accuracy charts.  
“MAE, RMSE, MAPE, bias; MAE by lead hours after gate; signed-error histogram; P90 band.”

**[8:00–9:00] Practices**  
“Public Insights API — no key. Cache + `POST /api/refresh`. Logical git history: scaffold → UI/metrics/docker → docs/deploy. AI-assisted build disclosed in README.”

**[9:00–10:00] Runbook**  
“`docker compose up --build` → localhost:8080. Smoke `/api/health`. Morning: Vercel login if needed, upload this script’s YouTube, paste URLs from SUBMISSION.md — do not forget the form is human-submitted.”
