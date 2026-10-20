from fastapi.testclient import TestClient
from apps.api.app.db.session import get_db_context


def test_api_ask_endpoint(client: TestClient, test_user):
    headers = test_user["headers"]

    # Retrieve an existing video ID
    with get_db_context() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM videos LIMIT 1")
            row = cur.fetchone()
            video_id = str(row["id"])

    # 1. Ask a question at pause_t = 12.5s
    resp = client.post(
        f"/api/v1/videos/{video_id}/ask",
        headers=headers,
        json={"query": "Can you explain this part?", "pause_t": 12.5},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "answer" in data
    assert "citations" in data
    assert "session_id" in data
    assert data["pause_t"] == 12.5

    # 2. Check message was saved in messages table with pause_t
    session_id = data["session_id"]
    with get_db_context() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT role, pause_t FROM messages WHERE session_id = %s", (session_id,))
            msgs = cur.fetchall()
            assert len(msgs) >= 2
            for m in msgs:
                assert m["pause_t"] == 12.5
