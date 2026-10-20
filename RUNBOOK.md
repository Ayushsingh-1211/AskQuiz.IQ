# RUNBOOK - what you do, in order (everything else is done by Antigravity)

## 0. One-time setup (Windows, about 30 min)
1. Install: Docker Desktop, Python 3.11, Node 20+, Git, ffmpeg+ffprobe (`winget install Gyan.FFmpeg`), Tesseract with `hin` language data (UB-Mannheim build), cloudflared (`winget install Cloudflare.cloudflared`), optional Ollama.
2. Get a Gemini API key from Google AI Studio. Open aistudio.google.com/rate-limit and note the real limits and current Flash / Flash-Lite model names (2.5 models shut down on 16 Oct 2026, so do not use them).
3. `git init` this folder. Copy `infra/.env.example` to `.env` and fill the key and model names.
4. Open this folder in Antigravity.

## 0b. Put your data in place (only you can do this)
- `eval/dataset/`: short clips (5-10 min each keeps quota and disk low): 1 talking-teacher video with captions, 1 slide lecture, 1 code tutorial, 1 handwritten-board clip, 1 Hinglish clip, plus 1 PDF, 1 PPT, notes. Use public/licensed material only (free Gemini tier may train on prompts).
- `eval/questions.json` labels: Antigravity drafts them at M3/M9, you review the gold answers.
- Resume PDF for testing the interview (use a sample, not a real private one).
- If your Antigravity version does not auto-read AGENTS.md, copy it to GEMINI.md (do not keep both loaded).

## 1. Design (Stitch), once
Follow `prompts/stitch/README.md` (6 prompts). Output goes in `DESIGN.md` and `design/`.

## 2. Build loop (repeat for M0 ... M9)
For each step: open a NEW Antigravity chat -> paste `prompts/00_MASTER.md` -> send `Run prompts/Mx.md` -> run the gate -> if it fails paste `prompts/FIX.md` with only the failing lines -> commit -> next step.
Do not start a step before the previous gate passes. Cut line: M0-M6 plus M9 evaluation are the core; M7 and M8 must really work for the 2X reward.

| Step | Prompt | Gate (from the plan) |
|---|---|---|
| M0 | prompts/M0.md | Self-check green on the hosted box |
| M1 | prompts/M1.md | Playback with seek; blocked YouTube URL still usable |
| M2 | prompts/M2.md | TAC unit tests pass; exact-word cut works |
| M3 | prompts/M3.md | 10-question text eval passes; spoiler leak = 0 |
| M4 | prompts/M4.md | Correct time sent on desktop and mobile |
| M5 | prompts/M5.md | Screen-only and silent-teacher tests pass |
| M6 | prompts/M6.md | PDF/PPT citations appear only after unlock |
| M7 | prompts/M7.md | Quiz questions cite sources; no templates |
| M8 | prompts/M8.md | Follow-ups depend on prior answers; explained scorecard |
| M9 | prompts/M9.md | All Section 8 targets recorded; fresh-clone setup works |
| Hosting | prompts/H.md (after M0, M3, M4, M9) | public smoke test passes |

## 3. Token-saving habits (already built in)
- AGENTS.md (always loaded) is under 3k characters; SPEC.md is a digest, so the agent never reads the .docx.
- One step per chat; each prompt lists the exact files to read and fill. STATUS.md lets a new chat resume in one read.
- Use the cheapest/fast model for scaffolding steps (M0, M1, M4, M7, M9, H) and the strongest for logic steps (M2, M3, M5, M6, M8). Planning mode off.
- Replies are capped at 5 lines; gates show failures only.
- Gemini free quota: pre-ingest demo videos, run the full eval once, cache everything.
- Stitch: 6 generations total, then edit prompts only.

## 4. Before the demo
`python infra/scripts/public_smoke.py`; laptop awake and plugged in; tunnel running; backup demo video recorded.
