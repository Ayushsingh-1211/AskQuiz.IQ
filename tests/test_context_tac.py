from apps.api.app.db.session import get_db_context
from core.context import build_context_pack
from core.tac import assert_no_future


def test_context_pack_tac_guarantee():
    with get_db_context() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM videos LIMIT 1")
            row = cur.fetchone()
            video_id = str(row["id"]) if row else "00000000-0000-0000-0000-000000000000"

        pause_t = 15.0
        pack, id_map = build_context_pack(conn, video_id, "What is being explained?", pause_t)

        # Context pack must satisfy TAC
        assert_no_future(pack, pause_t)
        assert pack["pause_t"] == pause_t
        for c in pack["chunks"]:
            assert c["visible_from_s"] <= pause_t + 1e-4
