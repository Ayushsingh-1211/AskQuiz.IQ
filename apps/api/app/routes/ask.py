import json
from typing import Any, Dict, Optional
import psycopg
from fastapi import APIRouter, Depends, HTTPException, status
from apps.api.app.config import get_settings
from apps.api.app.db.session import get_db
from apps.api.app.deps import get_current_user_id
from apps.api.app.errors import NotFoundError, ValidationError
from apps.api.app.logging import get_logger
from apps.api.app.schemas.ask import AskRequest, AskResponse
from core.answer import generate_answer

logger = get_logger("apps.api.ask")
router = APIRouter(prefix="/api/v1/videos", tags=["ask"])
settings = get_settings()


@router.post("/{video_id}/ask", response_model=AskResponse)
def ask_question(
    video_id: str,
    req: AskRequest,
    user_id: str = Depends(get_current_user_id),
    db: psycopg.Connection = Depends(get_db),
) -> AskResponse:
    if not req.query or not req.query.strip():
        raise ValidationError(message="Question query cannot be empty")

    pause_t = max(0.0, float(req.pause_t))

    with db.cursor() as cur:
        # Verify video exists
        cur.execute("SELECT id FROM videos WHERE id = %s", (video_id,))
        if not cur.fetchone():
            raise NotFoundError(message=f"Video {video_id} not found")

        # 1. Resolve or create chat session
        session_id = req.session_id
        if session_id:
            cur.execute("SELECT id FROM chat_sessions WHERE id = %s AND user_id = %s", (session_id, user_id))
            if not cur.fetchone():
                session_id = None

        if not session_id:
            cur.execute(
                """
                INSERT INTO chat_sessions (user_id, video_id, title)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (user_id, video_id, f"Session at {pause_t:.1f}s"),
            )
            session_id = str(cur.fetchone()["id"])

        # 2. Fetch history up to pause_t
        cur.execute(
            """
            SELECT role, content, pause_t
            FROM messages
            WHERE session_id = %s AND (pause_t IS NULL OR pause_t <= %s)
            ORDER BY created_at ASC
            """,
            (session_id, pause_t),
        )
        history = cur.fetchall()

    # 3. Generate answer under TAC
    answer_result = generate_answer(
        conn=db,
        video_id=video_id,
        query=req.query,
        pause_t=pause_t,
        chat_history=history,
    )

    # 4. Save messages
    with db.cursor() as cur:
        # Save user message
        cur.execute(
            """
            INSERT INTO messages (session_id, user_id, role, content, pause_t)
            VALUES (%s, %s, 'user', %s, %s)
            """,
            (session_id, user_id, req.query, pause_t),
        )

        # Save assistant message
        cur.execute(
            """
            INSERT INTO messages (session_id, user_id, role, content, pause_t, citations)
            VALUES (%s, %s, 'assistant', %s, %s, %s)
            """,
            (
                session_id,
                user_id,
                answer_result["answer"],
                pause_t,
                json.dumps(answer_result.get("citations", [])),
            ),
        )
    db.commit()

    return AskResponse(
        answer=answer_result["answer"],
        citations=answer_result.get("citations", []),
        used_pause_frame=answer_result.get("used_pause_frame", False),
        confidence=answer_result.get("confidence", "high"),
        refusal=answer_result.get("refusal", False),
        notes=answer_result.get("notes"),
        session_id=session_id,
        pause_t=pause_t,
    )
