from fastapi import APIRouter, Depends, Response

from leaderboard_api.auth.token import get_session_user, require_same_origin
from leaderboard_api.models.user import User
from leaderboard_api.repositories.users import update_display_name
from leaderboard_api.schemas.user import ProfileUpdate, UserProfile

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/check", response_model=UserProfile)
def check_user(response: Response, user: User = Depends(get_session_user)):
    response.headers["Cache-Control"] = "no-store"
    return user


@router.patch("/me", response_model=UserProfile, dependencies=[Depends(require_same_origin)])
def edit_profile(
    data: ProfileUpdate, response: Response, user: User = Depends(get_session_user)
):
    response.headers["Cache-Control"] = "no-store"
    return update_display_name(user.user_id, data.display_name)
