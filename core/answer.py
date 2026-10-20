from pathlib import Path
from typing import Any, Dict, List, Optional
import psycopg
from apps.api.app.config import get_settings
from apps.api.app.logging import get_logger
from core.context import build_context_pack
from core.llm.router import route_generate_json
from core.verifier import format_timestamp, verify_and_build_citations

logger = get_logger("core.answer")
settings = get_settings()

SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "answer_system.md"


def get_system_instruction() -> str:
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    return "Answer only from context. Never invent facts. Refuse if unsupported."


def generate_answer(
    conn: psycopg.Connection,
    video_id: str,
    query: str,
    pause_t: float,
    chat_history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Core answer pipeline under TAC:
    - Filters history by pause_t
    - Retrieves context pack
    - Routes to LLM
    - Verifies citations & TAC
    - Formats server citations
    """
    # 1. Filter chat history by messages.pause_t <= current pause_t
    valid_history = []
    if chat_history:
        for msg in chat_history:
            msg_t = msg.get("pause_t")
            if msg_t is None or float(msg_t) <= pause_t:
                valid_history.append(msg)

    # 2. Build context pack
    context_pack, id_map = build_context_pack(conn, video_id, query, pause_t)
    chunks = context_pack.get("chunks", [])
    recent_text = context_pack.get("recent_window", {}).get("text", "")

    refusal_msg = f"This isn't covered in the material up to {format_timestamp(pause_t)}."

    # If completely empty context, refuse directly
    if not chunks and not recent_text.strip():
        return {
            "answer": refusal_msg,
            "citations": [],
            "used_pause_frame": False,
            "confidence": "high",
            "refusal": True,
            "notes": "No material up to pause time",
        }

    # 3. Format prompt for LLM
    context_str_parts = []
    for c in chunks:
        context_str_parts.append(f"[{c['short_id']}] {c['text']}")

    context_str = "\n".join(context_str_parts)

    prompt = f"""
Current Pause Time: {format_timestamp(pause_t)} ({pause_t} seconds)

Recent Spoken Material (up to pause):
{recent_text}

Relevant Prior Context Chunks:
{context_str}

User Question:
{query}

Respond with JSON adhering to this structure:
{{
  "answer": "your factual response, or refusal if not covered in the material above",
  "citations": [{{"chunk_id": "<use exact short id from context, e.g. c2>"}}],
  "used_pause_frame": false,
  "confidence": "high|medium|low",
  "refusal": false,
  "notes": ""
}}

IMPORTANT: Use only short_ids that appear in the context above (e.g. c1, c2, c3...). Do NOT invent chunk_ids.
"""

    system_instruction = get_system_instruction()

    # 4. LLM Generation through router
    raw_result = route_generate_json(
        prompt=prompt,
        system_instruction=system_instruction,
    )

    is_refusal = raw_result.get("refusal", False)
    answer_text = raw_result.get("answer", "")

    if is_refusal or not answer_text or "not covered" in answer_text.lower():
        return {
            "answer": refusal_msg,
            "citations": [],
            "used_pause_frame": False,
            "confidence": raw_result.get("confidence", "high"),
            "refusal": True,
            "notes": raw_result.get("notes", ""),
        }

    # 5. Citation verification
    raw_citations = raw_result.get("citations", [])
    verified_citations, valid = verify_and_build_citations(raw_citations, id_map, pause_t)

    # If citations failed verification and answer relied on them, regenerate once or refuse
    if not valid and raw_citations and not verified_citations:
        logger.warning("All citations failed verification; downgrading to refusal")
        return {
            "answer": refusal_msg,
            "citations": [],
            "used_pause_frame": False,
            "confidence": "low",
            "refusal": True,
            "notes": "Citations invalid under TAC",
        }

    return {
        "answer": answer_text,
        "citations": verified_citations,
        "used_pause_frame": raw_result.get("used_pause_frame", False),
        "confidence": raw_result.get("confidence", "high"),
        "refusal": False,
        "notes": raw_result.get("notes", ""),
    }
