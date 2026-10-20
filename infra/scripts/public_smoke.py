import os
import sys
from pathlib import Path
import httpx

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from apps.api.app.config import get_settings


def main() -> int:
    settings = get_settings()
    api_url = os.getenv("PUBLIC_API_URL", settings.PUBLIC_API_URL).rstrip("/")
    print("=" * 60)
    print(f"AskQuiz.IQ Public Smoke Test -> {api_url}")
    print("=" * 60)

    client = httpx.Client(base_url=api_url, timeout=30.0)

    # 1. Health endpoint
    print("Testing GET /api/v1/health ...", end=" ")
    try:
        r_health = client.get("/api/v1/health")
        if r_health.status_code != 200:
            print(f"[FAIL] status {r_health.status_code}")
            return 1
        data = r_health.json()
        if data.get("status") != "ok":
            print(f"[FAIL] status={data.get('status')}")
            return 1
        print("[OK]")
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    # 2. Login endpoint
    print("Testing POST /api/v1/auth/login ...", end=" ")
    token = None
    try:
        r_login = client.post(
            "/api/v1/auth/login",
            json={"email": "demo@askquiz.iq", "password": "demo12345"},
        )
        if r_login.status_code != 200:
            print(f"[FAIL] status {r_login.status_code}: {r_login.text}")
            return 1
        login_data = r_login.json()
        token = login_data.get("access_token")
        if not token:
            print("[FAIL] No token in response")
            return 1
        print("[OK]")
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    headers = {"Authorization": f"Bearer {token}"}

    # 3. List videos
    print("Testing GET /api/v1/videos ...", end=" ")
    video_id = None
    try:
        r_vids = client.get("/api/v1/videos", headers=headers)
        if r_vids.status_code != 200:
            print(f"[FAIL] status {r_vids.status_code}")
            return 1
        vids = r_vids.json().get("items", [])
        if vids:
            video_id = vids[0]["id"]
            print(f"[OK] ({len(vids)} videos found)")
        else:
            print("[WARN] No videos in library, creating placeholder test video...")
            r_create = client.post(
                "/api/v1/videos",
                headers=headers,
                json={"title": "Demo Lecture", "url": "https://example.com/demo.mp4"},
            )
            video_id = r_create.json()["id"]
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    # 4. Ask endpoint
    print(f"Testing POST /api/v1/videos/{video_id}/ask ...", end=" ")
    try:
        r_ask = client.post(
            f"/api/v1/videos/{video_id}/ask",
            headers=headers,
            json={"query": "What is the topic?", "pause_t": 15.0},
        )
        if r_ask.status_code != 200:
            print(f"[FAIL] status {r_ask.status_code}: {r_ask.text}")
            return 1
        ask_data = r_ask.json()
        if "answer" not in ask_data or "pause_t" not in ask_data:
            print(f"[FAIL] Invalid ask response: {ask_data}")
            return 1
        print("[OK]")
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    print("=" * 60)
    print("All public smoke tests PASSED!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
