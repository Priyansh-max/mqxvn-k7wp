# Project context — Boreas / Reint take-home

## Goals

- Ship a polished day-ahead GB wind forecast desk for January 2026.
- Use only Elexon FUELHH (WIND) + WINDFOR stream data.
- Make forecast accuracy actionable for residual / thermal procurement.
- Deliver React + Python + Docker, public GitHub, docs/PDFs, silent demo.

## Constraints

- No Google form submission (human morning paste via SUBMISSION.md).
- Vercel-only cloud deploy; no Heroku.
- No YouTube publish overnight — silent MP4 + SPEAKER_SCRIPT.md only.
- Time-box mindset (~take-home overnight).

## Key decisions

- Product name **Boreas**; coastal North-Sea visual language (Fraunces + Outfit).
- Decision rule: latest WINDFOR with publishTime ≤ 09:20 CET on D−1.
- Residual band = P90 absolute error.
- Bake `jan2026_bundle.json` for reproducible boots.
- Repo name `mqxvn-k7wp` (random anonymous-style).

## Status notes

- Live Elexon Jan 2026 verified (1488 actual HH, 19053 forecast rows, 744 paired hourly points).
- Vercel token invalid overnight — morning login steps in SUBMISSION.md / README.
