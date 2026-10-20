from typing import Any, Dict, List, Optional
import psycopg
from psycopg.rows import dict_row
from apps.api.app.config import get_settings
from apps.api.app.logging import get_logger
from core.embeddings import embed_query
from core.tac import get_tac_sql_clause

logger = get_logger("core.retrieval")
settings = get_settings()


def hybrid_retrieve(
    conn: psycopg.Connection,
    video_id: str,
    query: str,
    pause_t: float,
    top_k: int = 8,
) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval: vector top 20 + FTS top 20 under TAC (visible_from_s <= pause_t),
    combined using Reciprocal Rank Fusion (RRF), returning top_k (default 8) chunks.
    Hard rule 1: every retrieval filters video_id = $1 AND visible_from_s <= $pause_t in SQL.
    """
    tac_clause = get_tac_sql_clause()  # "video_id = %s AND visible_from_s <= %s"

    # 1. Vector Search
    vector_results: List[Dict[str, Any]] = []
    try:
        q_emb = embed_query(query)
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT id, video_id, source_type, text, start_s, end_s, visible_from_s, page, slide, meta,
                       1 - (embedding <=> %s::vector) AS v_score
                FROM chunks
                WHERE {tac_clause}
                  AND embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector ASC
                LIMIT 20
                """,
                (q_emb, video_id, pause_t, q_emb),
            )
            vector_results = cur.fetchall()
    except Exception as exc:
        logger.warning(f"Vector search failed: {exc}")

    # 2. Full-Text Search (FTS)
    fts_results: List[Dict[str, Any]] = []
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT id, video_id, source_type, text, start_s, end_s, visible_from_s, page, slide, meta,
                       ts_rank(tsv, plainto_tsquery('simple', %s)) AS fts_score
                FROM chunks
                WHERE {tac_clause}
                  AND tsv @@ plainto_tsquery('simple', %s)
                ORDER BY fts_score DESC
                LIMIT 20
                """,
                (query, video_id, pause_t, query),
            )
            fts_results = cur.fetchall()
    except Exception as exc:
        logger.warning(f"FTS search failed: {exc}")

    # 3. Reciprocal Rank Fusion (RRF)
    k_constant = 60
    scores: Dict[str, float] = {}
    chunk_map: Dict[str, Dict[str, Any]] = {}

    for rank, item in enumerate(vector_results):
        cid = str(item["id"])
        chunk_map[cid] = item
        scores[cid] = scores.get(cid, 0.0) + (1.0 / (k_constant + rank + 1))

    for rank, item in enumerate(fts_results):
        cid = str(item["id"])
        chunk_map[cid] = item
        scores[cid] = scores.get(cid, 0.0) + (1.0 / (k_constant + rank + 1))

    if not chunk_map:
        return []

    # Sort chunks by RRF score
    sorted_cids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)

    # Ensure >=1 screen chunk if any matched
    selected: List[Dict[str, Any]] = []
    has_screen = False

    for cid in sorted_cids:
        chunk = chunk_map[cid]
        if chunk.get("source_type") == "screen":
            has_screen = True
        selected.append(chunk)
        if len(selected) >= top_k:
            break

    if not has_screen:
        # Check if there is a screen chunk in the rest of the candidates
        for cid in sorted_cids[top_k:]:
            if chunk_map[cid].get("source_type") == "screen":
                selected[-1] = chunk_map[cid]
                break

    return selected
