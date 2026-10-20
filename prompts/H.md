# H - Hosting: tunnel + Vercel + public smoke test (run after M0, M3, M4, M9)
Model: fast/cheap model. Planning mode: off. New chat for this step.
Read: AGENTS.md and spec/DEPLOY.md and the files below. Nothing else.
Fill ONLY these files (stub header `[H]` tells the purpose; delete the header when done):
- infra/tunnel/README.md
- infra/scripts/public_smoke.py
- apps/web/vercel.json
Do:
1. Tunnel: follow infra/tunnel/README.md; set PUBLIC_API_URL and ALLOWED_ORIGINS (add the Vercel URL) in .env; restart api.
2. Frontend: Vercel hobby from apps/web with VITE_API_URL = tunnel URL (vercel.json SPA rewrite), or run `npm run dev` locally.
3. public_smoke.py: health, login, ask against PUBLIC_API_URL.
4. Final demo prep: pre-ingest all demo videos, check quota at aistudio.google.com/rate-limit, laptop plugged in and awake, record a backup demo video.
Gate: `python infra/scripts/public_smoke.py` exits 0.
If a gate fails: fix only the owned files, rerun, show only the failing output. Reply max 5 lines (files changed, gate result, open issue). Append one line to STATUS.md.
