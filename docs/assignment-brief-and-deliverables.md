# Assignment Brief & Deliverables Checklist

## What was asked

UK energy utility take-home (day-ahead wholesale buyer):

1. Surface **latest / decision-relevant renewable (wind) generation forecasts** for day-ahead purchase decisions.
2. Provide **quantitative forecast accuracy** so the team can size thermal / residual procurement under uncertainty.

**Scope limits**

- National wind actuals + forecasts from **Elexon only** (FUELHH WIND + WINDFOR stream).
- Data relevant only for purchase decisions in **January 2026**.

**Stack requirements**

- React frontend, Python backend, Docker (`docker-compose`).
- Deploy sample app (Vercel preferred; no Heroku in this delivery).
- README with AI assistance disclosure.
- Architecture PDF + assignment brief PDF.
- Public GitHub repo with anonymous-style random name.
- Demo video materials (silent MP4 + speaker script; narrated YouTube left to submitter).

## What we were supposed to do

| Intent | Implementation |
| --- | --- |
| Avoid look-ahead bias | Decision rule: latest WINDFOR with `publishTime ≤ 09:20 CET on D−1` |
| Show forecast vs actual | Desk chart per delivery day |
| Make accuracy actionable | MAE, RMSE, MAPE, bias, P90 residual band |
| Ship reproducibly | Docker Compose + cached Jan 2026 bundle |
| Document clearly | README, architecture PDF, this brief |

## Actual deliverables checklist

- [x] Working React + FastAPI app (`frontend/`, `backend/`)
- [x] Elexon FUELHH / WINDFOR integration (public Insights API)
- [x] Decision-window methodology documented
- [x] Metrics: MAE, RMSE, MAPE, bias, lead-time / error distribution, residual band
- [x] Docker Compose local stack
- [x] README (map, start, AI tools, Elexon notes, methodology, live URL slot)
- [x] Architecture / design / tradeoffs doc (+ PDF)
- [x] Assignment brief / checklist doc (+ PDF)
- [x] Public GitHub repo `mqxvn-k7wp`
- [x] Logical overnight commit history
- [x] Silent demo MP4 + `SPEAKER_SCRIPT.md`
- [x] `SUBMISSION.md` with paste-ready URLs (no Google form submit)
- [ ] Live Vercel URL — *pending credentials; morning steps documented*
- [ ] Narrated unlisted YouTube — *submitter records from script/MP4*

## Out of scope (explicit)

- Submitting the Google form.
- Heroku deployment.
- YouTube upload.
- Non-Elexon data sources.
- Months other than January 2026 (except D−1 publish window spanning late Dec 2025).
