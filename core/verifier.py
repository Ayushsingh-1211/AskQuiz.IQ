import math
from typing import Any, Dict, List, Optional, Tuple
from apps.api.app.logging import get_logger

logger = get_logger("core.verifier")


def format_timestamp(seconds: Optional[float]) -> str:
    if seconds is None:
        return "00:00"
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def verify_and_build_citations(
    raw_citations: List[Dict[str, Any]],
    id_map: Dict[str, Dict[str, Any]],
    pause_t: float,
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Hard rule 2: The LLM returns chunk ids only. The server builds timestamps and page/slide numbers.
    Hard rule 3: Citation verifier and Pydantic schema validation stay on for every LLM output.
    """
    verified: List[Dict[str, Any]] = []
    is_valid = True

    for c in raw_citations:
        cid = str(c.get("chunk_id", "")).strip().lstrip("[").rstrip("]")
        chunk = id_map.get(cid)
        if not chunk:
            # Check by raw uuid if LLM used full uuid instead of short id
            for sc, cdata in id_map.items():
                if str(cdata.get("id")) == cid:
                    chunk = cdata
                    break

        if not chunk:
            logger.warning(f"Citation verification failed: chunk_id {cid} not in context pack")
            is_valid = False
            continue

        vis = float(chunk.get("visible_from_s", 0.0))
        if vis > pause_t + 1e-4:
            logger.warning(f"Citation verification failed: chunk {cid} violates TAC (vis={vis} > pause_t={pause_t})")
            is_valid = False
            continue

        source_type = chunk.get("source_type", "speech")
        start_s = chunk.get("start_s")
        end_s = chunk.get("end_s")
        page = chunk.get("page")
        slide = chunk.get("slide")

        # Server constructs the label and formatted coordinates
        if source_type == "speech":
            label = f"Video {format_timestamp(start_s)}-{format_timestamp(end_s)}"
        elif source_type == "screen":
            label = f"Screen {format_timestamp(start_s)}"
        elif source_type == "pdf" or page is not None:
            label = f"PDF p.{page or 1}"
        elif source_type == "ppt" or slide is not None:
            label = f"Slide {slide or 1}"
        else:
            label = f"Source {format_timestamp(start_s)}"

        verified.append({
            "chunk_id": str(chunk.get("id")),
            "text": chunk.get("text", "")[:300],
            "source_ref": {
                "source_type": source_type,
                "chunk_id": str(chunk.get("id")),
                "timestamp_s": start_s,
                "timestamp_formatted": format_timestamp(start_s),
                "page_number": page,
                "slide_number": slide,
                "label": label,
            },
        })

    return verified, is_valid
