import uuid
from typing import Any, Dict, Generator, Optional
from fastapi import Depends, Header, Request
import psycopg
from apps.api.app.auth import decode_access_token
from apps.api.app.db.session import get_db
from apps.api.app.errors import UnauthorizedError
from apps.api.app.logging import request_id_var


def get_request_id(x_request_id: Optional[str] = Header(None)) -> str:
    req_id = x_request_id or str(uuid.uuid4())
    request_id_var.set(req_id)
    return req_id


def get_current_user(
    request: Request,
    db: psycopg.Connection = Depends(get_db),
) -> Dict[str, Any]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise UnauthorizedError(
            message="Missing or invalid Authorization header",
            hint="Format must be 'Bearer <token>'",
        )

    token = auth_header.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError(message="Invalid token payload", hint="Token subject is missing")

    with db.cursor() as cur:
        cur.execute(
            "SELECT id, email, full_name, is_active FROM users WHERE id = %s",
            (user_id,),
        )
        user = cur.fetchone()

    if not user:
        raise UnauthorizedError(message="User not found", hint="User account may have been deleted")

    if not user["is_active"]:
        raise UnauthorizedError(message="User account is inactive", hint="Contact system administrator")

    return user


def get_current_user_id(current_user: Dict[str, Any] = Depends(get_current_user)) -> str:
    return str(current_user["id"])
