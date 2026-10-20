from typing import Any, Dict, List, Tuple
import psycopg
from apps.api.app.config import get_settings
from apps.api.app.logging import get_logger
from core.retrieval import hybrid_retrieve
from core.tac import assert_no_future, recent_window

logger = get_logger("core.context")
settings = get_settings()


def build_context_pack(
    conn: psycopg.Connection,
    video_id: str,
    query: str,
    pause_t: float,
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """
    Constructs the context pack for question answering under TAC enforcement:
    1. Hybrid retrieval (top 8)
    2. Recent window (60s, widen to 180s if <20 words)
    3. Context-local short IDs [c1], [c2]...
    4. Assert no future information
    """
    # 1. Retrieve candidate chunks
    retrieved_chunks = hybrid_retrieve(
        conn=conn,
        video_id=video_id,
        query=query,
        pause_t=pause_t,
        top_k=settings.TOPK,
    )

    # 2. Get recent window
    rw = recent_window(
        conn=conn,
        video_id=video_id,
        pause_t=pause_t,
        window_s=settings.RECENT_WINDOW_S,
        min_words=settings.RECENT_MIN_WORDS,
        wide_window_s=settings.RECENT_WINDOW_WIDE_S,
    )

    # 3. Context-local ID mapping
    id_map: Dict[str, Dict[str, Any]] = {}
    formatted_chunks: List[Dict[str, Any]] = []

    total_chars = len(rw.get("text", ""))

    for idx, c in enumerate(retrieved_chunks, start=1):
        short_id = f"c{idx}"
        chunk_text = c.get("text", "")
        # Approximate 4 chars per token, check context cap
        if (total_chars + len(chunk_text)) // 4 > settings.CONTEXT_TOKEN_CAP:
            break

        total_chars += len(chunk_text)
        id_map[short_id] = c

        formatted_chunks.append({
            "short_id": short_id,
            "id": str(c["id"]),
            "source_type": c.get("source_type"),
            "text": chunk_text,
            "start_s": c.get("start_s"),
            "end_s": c.get("end_s"),
            "visible_from_s": float(c.get("visible_from_s", 0.0)),
            "page": c.get("page"),
            "slide": c.get("slide"),
        })

    context_pack = {
        "video_id": video_id,
        "pause_t": pause_t,
        "recent_window": rw,
        "chunks": formatted_chunks,
    }

    # 4. Strict TAC assertion before returning
    assert_no_future(context_pack, pause_t)

    return context_pack, id_map
