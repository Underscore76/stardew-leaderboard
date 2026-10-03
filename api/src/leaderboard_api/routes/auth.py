import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from leaderboard_api.config import discord_config, get_settings
from leaderboard_api.auth.token import (
    SESSION_COOKIE,
    delete_session,
    require_same_origin,
    session_from_discord_token,
)

router = APIRouter(prefix="/user", tags=["auth"])
STATE_COOKIE = "sdv_discord_state"


def set_cookie(response: Response, key: str, value: str, max_age: int) -> None:
    response.set_cookie(
        key,
        value,
        max_age=max_age,
        path="/",
        secure=get_settings().secure_cookies,
        httponly=True,
        samesite="lax",
    )


def login_result(error: str | None = None) -> RedirectResponse:
    path = f"/login?{urlencode({'error': error})}" if error else "/profile"
    response = RedirectResponse(f"{get_settings().frontend_url}{path}", status_code=303)
    response.delete_cookie(STATE_COOKIE, path="/")
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/login")
def start_login():
    try:
        config = discord_config()
    except ValueError:
        return login_result("not_configured")
    state = secrets.token_urlsafe(32)
    query = urlencode(
        {
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "response_type": "code",
            "scope": "identify",
            "state": state,
        }
    )
    response = RedirectResponse(f"https://discord.com/oauth2/authorize?{query}")
    response.headers["Cache-Control"] = "no-store"
    set_cookie(response, STATE_COOKIE, state, 600)
    return response


@router.get("/callback")
def callback(request: Request, code: str = "", state: str = "", error: str = ""):
    expected = request.cookies.get(STATE_COOKIE, "")
    if not state or not expected or not secrets.compare_digest(state, expected):
        return login_result("invalid_state")
    if error:
        return login_result("denied")
    if not code:
        return login_result("login_failed")
    try:
        config = discord_config()
    except ValueError:
        return login_result("not_configured")

    try:
        with httpx.Client(timeout=10) as client:
            token_response = client.post(
                "https://discord.com/api/v10/oauth2/token",
                data={**config, "grant_type": "authorization_code", "code": code},
            )
        token_response.raise_for_status()
        session = session_from_discord_token(
            token_response.json()["access_token"]
        )
    except (httpx.HTTPError, HTTPException, KeyError, ValueError):
        return login_result("login_failed")

    delete_session(request)
    response = login_result()
    set_cookie(response, SESSION_COOKIE, session.session_id, get_settings().session_duration_seconds)
    return response


@router.post("/logout", status_code=204, dependencies=[Depends(require_same_origin)])
def logout(request: Request):
    delete_session(request)
    response = Response(status_code=204)
    response.delete_cookie(
        SESSION_COOKIE, path="/", secure=get_settings().secure_cookies, httponly=True, samesite="lax"
    )
    return response
