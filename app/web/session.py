import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Response

COOKIE_NAME = "JSESSIONID"
SESSION_TTL_MINUTES = 60 * 24  # 24 hours

# Server-side session store: session_id -> {"user_id": int, "expires": datetime}
_sessions: dict[str, dict] = {}


def create_session(user_id: int, response: Response) -> str:
    """Create a server-side session for the given user and set the cookie on the response."""
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "user_id": user_id,
        "expires": datetime.utcnow() + timedelta(minutes=SESSION_TTL_MINUTES),
    }
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=SESSION_TTL_MINUTES * 60,
    )
    return session_id


def get_user_id_from_session(session_id: Optional[str]) -> Optional[int]:
    """Return the user_id bound to this session, or None if missing/expired."""
    if not session_id:
        return None
    session = _sessions.get(session_id)
    if not session:
        return None
    if datetime.utcnow() > session["expires"]:
        _sessions.pop(session_id, None)
        return None
    return session["user_id"]


def destroy_session(session_id: str, response: Response) -> None:
    """Invalidate the session and clear the cookie."""
    _sessions.pop(session_id, None)
    response.delete_cookie(COOKIE_NAME)
