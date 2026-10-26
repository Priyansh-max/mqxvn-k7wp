# Morning submission paste sheet

**Do not auto-submit the Google form.** Copy these fields when ready.

## URLs

| Field | Value |
| --- | --- |
| GitHub repository | https://github.com/Priyansh-max/mqxvn-k7wp |
| Live app URL | _TBD after Vercel deploy_ |
| Demo video | _TBD — upload `media/boreas-demo-silent.mp4` (or your narrated cut) as **unlisted** YouTube; script in `SPEAKER_SCRIPT.md`_ |
| Architecture PDF | in-repo `docs/architecture-and-tradeoffs.pdf` |
| Assignment brief PDF | in-repo `docs/assignment-brief-and-deliverables.pdf` |

## Local paths (this machine)

- Project: `D:\Personal_Projects\reint-assignment`
- Silent MP4: `D:\Personal_Projects\reint-assignment\media\boreas-demo-silent.mp4`

## Vercel morning steps (credentials were invalid overnight)

1. `npm i -g vercel@latest`
2. `vercel login` (Rajika’s account)
3. From repo root: `vercel --prod`
4. Confirm `/api/health` on the deployment host
5. Paste the production URL into this file and the Google form
6. If Python serverless fails, deploy FE only and set `VITE_API_BASE` to a reachable API, or demo via Docker / port-forward and note “local Docker verified” in the form comments

## Verified overnight

- [x] Elexon Jan 2026 FUELHH + WINDFOR live fetch
- [x] API `/api/health` + `/api/overview` locally
- [x] Frontend production build
- [x] Public GitHub repo
- [ ] Docker compose smoke _(run before submit if not green overnight)_
- [ ] Vercel production URL
- [ ] YouTube unlisted link
