import secrets
from datetime import datetime

from pydantic import computed_field
from leaderboard_api.models.base import StardewBaseModel
from leaderboard_api.utils import current_timestamp
from leaderboard_api.config import get_settings


class Session(StardewBaseModel):
    session_id: str
    user_id: str
    created_at: int
    ttl: int

    @property
    def pk(self) -> str:
        return f"SESSION#{self.session_id}"

    @property
    def sk(self) -> str:
        return f"USER#{self.user_id}"

    @staticmethod
    def create(user_id: str) -> "Session":
        session_id = secrets.token_urlsafe(32)

        created_at = current_timestamp()
        ttl = created_at + get_settings().session_duration_seconds
        return Session(
            session_id=session_id,
            user_id=user_id,
            created_at=created_at,
            ttl=ttl,
        )

    def is_expired(self) -> bool:
        return self.ttl <= current_timestamp()
