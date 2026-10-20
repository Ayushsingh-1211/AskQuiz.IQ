import json
from typing import Any, Dict, List
import psycopg
from core.chunking import chunk_words


def create_chunks_for_video(
    conn: psycopg.Connection,
    video_id: str,
    words: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Chunks words and inserts speech chunks into the chunks table.
    """
    chunks = chunk_words(words)
    if not chunks:
        return []

    with conn.cursor() as cur:
        # Delete old speech chunks for this video if any
        cur.execute("DELETE FROM chunks WHERE video_id = %s AND source_type = 'speech'", (video_id,))

        for c in chunks:
            cur.execute(
                """
                INSERT INTO chunks (video_id, source_type, text, start_s, end_s, visible_from_s, meta)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    video_id,
                    c["source_type"],
                    c["text"],
                    c["start_s"],
                    c["end_s"],
                    c["visible_from_s"],
                    json.dumps(c["meta"]),
                ),
            )
            c["id"] = str(cur.fetchone()["id"])
    conn.commit()
    return chunks
