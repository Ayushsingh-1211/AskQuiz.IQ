# AskQuiz.IQ — Zero-Cost (₹0) Production Deployment Guide
**Architecture:** Vercel (React Frontend) + Render Free (FastAPI Backend) + Neon Free (PostgreSQL + pgvector)

---

## Overview & ₹0 Cost Verification
- **Frontend:** Vercel Hobby Free Plan (Global CDN, HTTPS, 100GB bandwidth/mo).
- **Backend:** Render Free Web Service (Docker runtime, 512MB RAM, automatic TLS).
- **Worker/Retrieval Mode:** Cloud-safe PostgreSQL Full-Text Search (FTS) retrieval under TAC (`EMBEDDING_BACKEND=fts`).
- **Database:** Neon Free Serverless PostgreSQL (0.5GB storage, pgvector included).
- **Queue/Broker:** Native PostgreSQL `jobs` table (`SKIP LOCKED`). **Zero Redis required**.
- **LLM:** Google Gemini Free Tier via `core/llm` provider.
- **Laptop Independence:** Works 24/7 when your laptop is turned off.

> [!IMPORTANT]
> **Render Free 512MB RAM Constraint & Upload Processing Limitation:**
> Render Free web services provide 512 MB of RAM. Processing newly uploaded raw video files (running local speech recognition models like Whisper and OCR) requires >800MB RAM and triggers immediate Out-Of-Memory (OOM SIGKILL 137).
> To guarantee 100% uptime and sub-second responses within 512MB RAM, configure `EMBEDDING_BACKEND=fts` and `EMBEDDED_WORKER=false`. The web API runs at ~100MB RAM, and the pre-seeded demo video (**Talking Teacher - Machine Learning Intro**) with its 25 chunks is pre-loaded and ready for instant playback, streaming, full-text retrieval under TAC, and Gemini Q&A with timestamp citations. Newly uploaded videos will be queued in the database but cannot be processed by the free web service.

---

## Step 1: Create Free Database on Neon (2 Minutes)

1. Go to [https://neon.tech](https://neon.tech) and sign up with GitHub or Google.
2. Click **Create Project**:
   - **Project Name:** `askquiz-db`
   - **Postgres version:** 16 (default)
   - **Region:** Choose closest to your users (e.g., `AWS US East (N. Virginia)` or `AWS Europe (Frankfurt)`).
3. Once created, you will see your **Connection Details** on the Dashboard.
4. Select **Connection string** and check **Pooled connection** or direct connection:
   - Example format:
     ```text
     postgresql://neondb_owner:npg_xxxx@ep-xyz-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
     ```
5. Copy this URL. This is your `DATABASE_URL`. (Keep it private!).

*(Note: The AskQuiz.IQ backend automatically enables `pgvector`, runs all table migrations, seeds the demo user `demo@askquiz.iq / demo12345`, and seeds demo video chunks on first startup).*

---

## Step 2: Deploy Backend on Render Free (4 Minutes)

1. Go to [https://render.com](https://render.com) and sign in with GitHub.
2. Click **New +** at the top right and select **Web Service** (or **Blueprint** using `render.yaml`).
3. Select **Build and deploy from a Git repository** and connect:
   - Repository: `Ayushsingh-1211/AskQuiz.IQ`
4. Configure the service:
   - **Name:** `askquiz-api` (or your choice)
   - **Region:** Same as Neon (e.g. `Oregon (US West)` or `Frankfurt (EU)`)
   - **Branch:** `main`
   - **Root Directory:** *(leave blank)*
   - **Language / Runtime:** Select **Docker**
   - **Dockerfile Path:** `./infra/Dockerfile`
   - **Docker Build Context:** `.` (root directory)
   - **Instance Type:** Select **Free** ($0/month)
5. Scroll down to **Environment Variables** and configure:
   | Key | Value | Notes |
   |---|---|---|
   | `DATABASE_URL` | *(paste your Neon URL from Step 1)* | Must include `?sslmode=require` |
   | `GEMINI_API_KEY` | *(your Gemini API key)* | From Google AI Studio |
   | `JWT_SECRET` | *(use Render's auto-generated secret or run `openssl rand -hex 32`)* | Never use a hardcoded secret in production |
   | `ALLOWED_ORIGINS` | `https://askquiz-iq.vercel.app,http://localhost:5173` | Add your Vercel URL here |
   | `EMBEDDING_BACKEND` | `fts` | Uses PostgreSQL full-text search; avoids 400MB local ML model |
   | `EMBEDDED_WORKER` | `false` | Keeps memory <120MB on Render Free (512MB RAM ceiling) |
   | `AUTO_SEED_DEMO` | `true` | Pre-seeds demo video & 25 chunks on first boot |
   | `WEB_CONCURRENCY` | `1` | Single Uvicorn process to prevent memory multiplication |
   | `ANSWER_MODEL` | `gemini-3.5-flash-lite` | Free tier fast model |
   | `VISION_MODEL` | `gemini-3.5-flash-lite` | Vision model |
   | `LLM_FALLBACK_CHAIN` | `gemini-3.5-flash-lite,gemini-3.5-flash` | Automatic fallback |
   | `DATA_DIR` | `/app/data` | Container data directory |

6. Click **Deploy Web Service**.
7. Wait 2-3 minutes for the Docker image to build. Once live, Render gives you a public URL, for example:
   ```text
   https://askquiz-api.onrender.com
   ```
8. **Verify Backend Health:**
   Visit `https://askquiz-api.onrender.com/api/v1/health` in your browser.
   It should return:
   ```json
   {"status":"ok","database":true,"embedding_backend":"fts"}
   ```

---

## Step 3: Deploy Frontend on Vercel Free (3 Minutes)

1. Go to [https://vercel.com](https://vercel.com) and sign in with GitHub.
2. Click **Add New...** → **Project**.
3. Import your GitHub repository: `Ayushsingh-1211/AskQuiz.IQ`.
4. In the Project Configuration:
   - **Project Name:** `askquiz-iq` (or your choice)
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click Edit and select `apps/web`
   - **Build and Output Settings:** Leave default (`npm run build`, `dist`)
5. Open **Environment Variables**:
   - Add `VITE_API_URL`
   - Value: Your Render backend URL from Step 2 (e.g. `https://askquiz-api.onrender.com`)
   *(Do NOT add a trailing slash)*
6. Click **Deploy**.
7. In ~45 seconds, Vercel will give you a public URL:
   ```text
   https://askquiz-iq.vercel.app
   ```

---

## Step 4: Final 1-Minute Link Check

1. Copy your Vercel URL (e.g. `https://askquiz-iq.vercel.app`).
2. Go back to Render Dashboard → `askquiz-api` → **Environment**.
3. Ensure `ALLOWED_ORIGINS` contains your exact Vercel URL:
   ```text
   https://askquiz-iq.vercel.app,http://localhost:5173
   ```
   *(Note: The backend CORS regex also automatically allows all `*.vercel.app` domains).*

---

## Step 5: Test the Live Application

1. Open your live Vercel URL in an incognito window or phone.
2. Sign in with the documented demo credentials:
   - **Email:** `demo@askquiz.iq`
   - **Password:** `demo12345`
3. You will see the video library containing **Talking Teacher - Machine Learning Intro**.
4. Click on the video to open the **Watch & Ask** workspace.
5. Seek to `02:00` or `04:00` on the video player.
6. Ask a question in the chat box:
   - *"What is machine learning?"* or *"What did the instructor explain about supervised learning?"*
7. Confirm that:
   - The assistant answers using the video transcript.
   - Citations show exact timestamps (e.g., `01:45`).
   - Clicking a citation seeks the video to that moment.
   - Questions about future parts of the video are safely refused under TAC.
