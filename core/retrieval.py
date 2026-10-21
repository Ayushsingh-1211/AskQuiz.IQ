import re
from typing import Any, Dict, List, Optional
import psycopg
from psycopg.rows import dict_row
from apps.api.app.config import get_settings
from apps.api.app.logging import get_logger
from core.tac import get_tac_sql_clause

logger = get_logger("core.retrieval")

# Common English conversational/filler tokens to ignore when building the OR tsquery
_STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "explain", "few", "for", "from", "further", "had", "hadn't",
    "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's",
    "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how",
    "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't",
    "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
    "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "tell", "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "video", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've",
    "were", "weren't", "what", "what's", "when", "when's", "where", "where's",
    "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
    "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your",
    "yours", "yourself", "yourselves",
}


def _extract_tsquery_terms(query: str) -> Optional[str]:
    """Extracts alphanumeric tokens of length >= 3 and joins them with OR (|)."""
    tokens = re.findall(r"[a-zA-Z0-9]+", query.lower())
    meaningful = [t for t in tokens if len(t) >= 3 and t not in _STOP_WORDS]
    if not meaningful:
        meaningful = [t for t in tokens if len(t) >= 3]
    if not meaningful:
        return None
    unique_tokens = list(dict.fromkeys(meaningful))
    return " | ".join(unique_tokens[:8])


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
    When EMBEDDING_BACKEND=fts, vector search is skipped entirely to prevent loading SentenceTransformer.
    """
    settings = get_settings()
    is_fts_mode = (settings.EMBEDDING_BACKEND.lower() == "fts")
    tac_clause = get_tac_sql_clause()  # "video_id = %s AND visible_from_s <= %s"

    # 1. Vector Search (skipped in FTS mode to avoid loading SentenceTransformer/PyTorch)
    vector_results: List[Dict[str, Any]] = []
    if not is_fts_mode:
        try:
            from core.embeddings import embed_query
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
            # 2a. Primary search using plainto_tsquery
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

            # 2b. If fewer than top_k results, attempt OR tsquery fallback
            if len(fts_results) < top_k:
                or_terms = _extract_tsquery_terms(query)
                if or_terms:
                    existing_cids = {str(r["id"]) for r in fts_results}
                    cur.execute(
                        f"""
                        SELECT id, video_id, source_type, text, start_s, end_s, visible_from_s, page, slide, meta,
                               ts_rank(tsv, to_tsquery('simple', %s)) AS fts_score
                        FROM chunks
                        WHERE {tac_clause}
                          AND tsv @@ to_tsquery('simple', %s)
                        ORDER BY fts_score DESC
                        LIMIT 20
                        """,
                        (or_terms, video_id, pause_t, or_terms),
                    )
                    for r in cur.fetchall():
                        if str(r["id"]) not in existing_cids:
                            fts_results.append(r)
                            existing_cids.add(str(r["id"]))

            # 2c. If still empty in FTS mode, fall back to recent chunks prior to pause_t
            if not fts_results and is_fts_mode:
                cur.execute(
                    f"""
                    SELECT id, video_id, source_type, text, start_s, end_s, visible_from_s, page, slide, meta,
                           0.1 AS fts_score
                    FROM chunks
                    WHERE {tac_clause}
                    ORDER BY visible_from_s DESC
                    LIMIT %s
                    """,
                    (video_id, pause_t, top_k),
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
        for cid in sorted_cids[top_k:]:
            if chunk_map[cid].get("source_type") == "screen":
                selected[-1] = chunk_map[cid]
                break

    return selected
