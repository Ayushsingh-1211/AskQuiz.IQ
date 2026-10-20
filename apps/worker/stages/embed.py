from typing import List
import psycopg
from core.embeddings import embed_passages


def embed_video_chunks(conn: psycopg.Connection, video_id: str, batch_size: int = 32) -> int:
    """
    Finds chunks without embeddings for video_id and computes 384-d vectors using multilingual-e5-small.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, text
            FROM chunks
            WHERE video_id = %s AND embedding IS NULL
            ORDER BY visible_from_s ASC
            """,
            (video_id,),
        )
        rows = cur.fetchall()

    if not rows:
        return 0

    chunk_ids = [str(r["id"]) for r in rows]
    texts = [r["text"] for r in rows]

    embeddings = embed_passages(texts, batch_size=batch_size)

    with conn.cursor() as cur:
        for cid, emb in zip(chunk_ids, embeddings):
            cur.execute(
                """
                UPDATE chunks
                SET embedding = %s::vector
                WHERE id = %s
                """,
                (emb, cid),
            )
    conn.commit()
    return len(chunk_ids)
