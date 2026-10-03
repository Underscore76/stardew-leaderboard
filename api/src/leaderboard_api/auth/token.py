import httpx
from fastapi import Depends, HTTPException, Request

from leaderboard_api.config import get_settings
from leaderboard_api.models.user import User
from leaderboard_api.repositories.users import get_user, sync_discord_user
from leaderboard_api.repositories import sessions
from leaderboard_api.models.session import Session

SESSION_COOKIE = "sdv_speedrun_session"


def require_same_origin(request: Request) -> None:
    if request.headers.get("origin") != get_settings().frontend_origin:
        raise HTTPException(status_code=403, detail="Invalid request origin")


def session_from_discord_token(token: str) -> Session:
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(
                "https://discord.com/api/v10/users/@me",
                headers={"Authorization": f"Bearer {token}"},
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Discord is unavailable") from exc
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Discord token")
    data = response.json()
    user = sync_discord_user(
        user_id=data["id"],
        username=data["username"],
        avatar=data.get("avatar"),
        display_name=data.get("global_name") or data["username"],
    )
    return sessions.create_session(Session.create(user_id=user.user_id))


def get_session_user(request: Request) -> User:
    session_id = request.cookies.get(SESSION_COOKIE)
    if not session_id:
        raise HTTPException(status_code=401, detail="Not signed in")
    session = sessions.get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session invalid")
    if session.is_expired():
        sessions.delete_session(session)
        raise HTTPException(status_code=401, detail="Session expired")
    user = get_user(session.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def delete_session(request: Request, session_cookie: str = SESSION_COOKIE) -> None:
    session_id = request.cookies.get(session_cookie)
    if session_id:
        session = sessions.get_session(session_id)
        if session:
            sessions.delete_session(session)


def require_admin(user: User = Depends(get_session_user)) -> User:
    """Use on future admin endpoints in addition to origin checks for mutations."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
