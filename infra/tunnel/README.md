# Cloudflare Tunnel Setup for AskQuiz.IQ

## Quick Tunnel (Ephemeral $0 mode)
To expose the local API publicly:
```bash
cloudflared tunnel --url http://localhost:8000
```
This prints a `https://<random-name>.trycloudflare.com` URL.

To expose the web frontend publicly:
```bash
cloudflared tunnel --url http://localhost:5173
```
Or build and serve with `npx vite preview --port 5173`.
