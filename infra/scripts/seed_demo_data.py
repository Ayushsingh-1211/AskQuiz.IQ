import json
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from apps.api.app.db.session import get_db_context
from apps.api.app.logging import get_logger
from apps.worker.stages.asr import parse_srt_to_words
from apps.worker.stages.chunk import create_chunks_for_video
from apps.worker.stages.embed import embed_video_chunks

logger = get_logger("infra.seed_demo")

DEMO_VIDEO_ID = "1ba5b57f-4aad-489d-9948-3d6ab873055e"
DEMO_TITLE = "Talking Teacher - Machine Learning Intro"
DEMO_DURATION = 374.16


def seed_demo_data() -> None:
    srt_path = repo_root / "eval" / "dataset" / "talking_teacher.en.srt"
    if not srt_path.exists():
        logger.warning(f"Demo subtitle file not found at {srt_path}")
        return

    with get_db_context() as conn:
        with conn.cursor() as cur:
            # 1. Get or create demo user
            cur.execute("SELECT id FROM users WHERE email = 'demo@askquiz.iq'")
            user = cur.fetchone()
            if not user:
                logger.info("Demo user not found, running seed_users first...")
                from infra.scripts.seed_users import seed_users
                seed_users()
                cur.execute("SELECT id FROM users WHERE email = 'demo@askquiz.iq'")
                user = cur.fetchone()

            if not user:
                logger.error("Could not obtain demo user for video seeding")
                return

            demo_user_id = user["id"]

            # 2. Check if demo video already exists
            cur.execute("SELECT id FROM videos WHERE id = %s", (DEMO_VIDEO_ID,))
            existing = cur.fetchone()
            if existing:
                cur.execute("SELECT count(*) FROM chunks WHERE video_id = %s", (DEMO_VIDEO_ID,))
                chunk_count = cur.fetchone()["count"]
                if chunk_count > 0:
                    logger.info(f"Demo video already seeded ({chunk_count} chunks present)")
                    return

            # Insert or update video
            cur.execute(
                """
                INSERT INTO videos (id, user_id, title, duration_s, status, metadata)
                VALUES (%s, %s, %s, %s, 'ready_text', %s)
                ON CONFLICT (id) DO UPDATE
                SET status = 'ready_text', duration_s = EXCLUDED.duration_s
                """,
                (
                    DEMO_VIDEO_ID,
                    demo_user_id,
                    DEMO_TITLE,
                    DEMO_DURATION,
                    json.dumps({"source": "demo_seed", "visual_unavailable": False}),
                ),
            )
        conn.commit()

        # 3. Create chunks and compute embeddings
        logger.info(f"Seeding demo video chunks from {srt_path.name}...")
        words = parse_srt_to_words(srt_path)
        chunks = create_chunks_for_video(conn, DEMO_VIDEO_ID, words)
        logger.info(f"Created {len(chunks)} chunks for demo video")

        embedded = embed_video_chunks(conn, DEMO_VIDEO_ID)
        logger.info(f"Successfully embedded {embedded} chunks with E5 model for demo video")


if __name__ == "__main__":
    seed_demo_data()
