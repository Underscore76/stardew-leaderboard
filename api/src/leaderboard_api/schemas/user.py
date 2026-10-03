from pydantic import BaseModel, ConfigDict, Field


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    username: str
    avatar: str | None = None
    display_name: str | None = None
    is_admin: bool = False


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    display_name: str = Field(min_length=1, max_length=64)
