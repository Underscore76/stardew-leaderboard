from leaderboard_api.models.base import StardewBaseModel


class User(StardewBaseModel):
    user_id: str
    username: str
    avatar: str | None = None
    display_name: str | None = None
    is_admin: bool = False

    @property
    def pk(self) -> str:
        return "PROFILE"

    @property
    def sk(self) -> str:
        return f"USER#{self.user_id}"

