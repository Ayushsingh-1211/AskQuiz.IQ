from typing import Any, Dict, List, Optional
import psycopg
from psycopg.rows import dict_row
from apps.api.app.logging import get_logger

logger = get_logger("core.tac")


def get_tac_sql_clause() -> str:
    """Hard rule 1: every retrieval filters video_id = $1 AND visible_from_s <= $pause_t."""
    return "video_id = %s AND visible_from_s <= %s"


def trim_at_word(words: List[Dict[str, Any]], pause_t: float) -> List[Dict[str, Any]]:
    """
    Trims word list so only words started up to pause_t are included.
    Exact-word cut ensures nothing beyond pause_t is spoken.
    """
    if not words:
        return []
    return [w for w in words if float(w.get("start", 0.0)) <= pause_t]


def recent_window(
    conn: psycopg.Connection,
    video_id: str,
    pause_t: float,
    window_s: float = 60.0,
    min_words: int = 20,
    wide_window_s: float = 180.0,
) -> Dict[str, Any]:
    """
    Extracts speech context immediately preceding pause_t, trimmed at the exact word.
    If fewer than min_words found, widens window to wide_window_s.
    """
    start_t = max(0.0, pause_t - window_s)

    with conn.cursor(row_factory=dict_row) as cur:
        # Retrieve speech chunks whose span overlaps [start_t, pause_t]
        cur.execute(
            """
            SELECT text, start_s, end_s, visible_from_s, meta
            FROM chunks
            WHERE video_id = %s
              AND source_type = 'speech'
              AND start_s <= %s
              AND end_s >= %s
            ORDER BY start_s ASC
            """,
            (video_id, pause_t, start_t),
        )
        rows = cur.fetchall()

    words: List[Dict[str, Any]] = []
    for r in rows:
        meta = r.get("meta") or {}
        chunk_words = meta.get("words", [])
        for w in chunk_words:
            if w.get("start", 0.0) >= start_t and w.get("start", 0.0) <= pause_t:
                words.append(w)

    # Deduplicate words by (start, end, word)
    unique_words = []
    seen = set()
    for w in words:
        k = (w.get("start"), w.get("end"), w.get("word"))
        if k not in seen:
            seen.add(k)
            unique_words.append(w)

    unique_words.sort(key=lambda x: x.get("start", 0.0))
    trimmed = trim_at_word(unique_words, pause_t)

    # If < min_words and we haven't widened yet, widen window
    if len(trimmed) < min_words and window_s < wide_window_s:
        return recent_window(conn, video_id, pause_t, window_s=wide_window_s, min_words=min_words, wide_window_s=wide_window_s)

    text = " ".join(w["word"].strip() for w in trimmed)
    return {
        "text": text,
        "words": trimmed,
        "start_s": trimmed[0]["start"] if trimmed else start_t,
        "end_s": trimmed[-1]["end"] if trimmed else pause_t,
        "word_count": len(trimmed),
    }


def assert_no_future(context_pack: Dict[str, Any], pause_t: float) -> None:
    """
    TAC strict assertion: no retrieved chunk or word may exceed pause_t.
    """
    chunks = context_pack.get("chunks", [])
    epsilon = 1e-4

    for c in chunks:
        vis = float(c.get("visible_from_s", 0.0))
        if vis > pause_t + epsilon:
            msg = f"TAC VIOLATION: chunk {c.get('id')} visible_from_s={vis} > pause_t={pause_t}"
            logger.critical(msg)
            raise AssertionError(msg)

    # Check recent window words if present
    recent = context_pack.get("recent_window") or {}
    for w in recent.get("words", []):
        w_start = float(w.get("start", 0.0))
        if w_start > pause_t + epsilon:
            msg = f"TAC VIOLATION: word '{w.get('word')}' start={w_start} > pause_t={pause_t}"
            logger.critical(msg)
            raise AssertionError(msg)
