# STATUS.md - one line per finished step (agent appends). New chat? Read only this + AGENTS.md.
- M0: Foundation, config, DB migrations, auth, health check, tunnel all green.
- M1: Video intake, jobs, audio/proxy transcoding, Range 206 streaming green.
- M2: Chunks schema 002, ASR/captions, chunking, E5 embeddings, TAC exact-word cut green.
- M3: Retrieval, Gemini router, answer pipeline, citation verifier, 0-spoiler-leak eval green.
- M4: React player, Pause & Ask UI, AskBox vitest, Vite clean build green.
- H: Cloudflare tunnel, Vite frontend deployment, public smoke test against live tunnel green.
- Incident Fix: Video playback, Range 206 streaming proxy, WebVTT captions endpoint, and Cloudflare tunnel verified green.
- Master Repair: Worker pipeline (Whisper ASR, chunks, E5 embeddings), PyAV compatibility fix, Watch page polling, 5-question TAC eval green.
- Live Deployment: Public frontend & backend Cloudflare tunnels, dict_row & 4-arg vector retrieval fix, Gemini 3.5 fallback chain, WebVTT captions DB fallback, video-grounded QA & citations all verified green.
- Login Fix: Demo password reset to demo12345 with dual alias support, 4/4 auth regression tests pass, live public authentication and workspace navigation verified green.






