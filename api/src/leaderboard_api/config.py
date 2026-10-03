import os
from functools import lru_cache
from typing import Self
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

from leaderboard_api.services.secrets import get_secrets
from leaderboard_api.services.ssm import get_ssm_param_value


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, hide_input_in_errors=True)

    frontend_url: str = "http://localhost:5173"
    discord_redirect_uri: str | None = None
    discord_client_id: str = ""
    discord_client_secret: SecretStr = SecretStr("")
    discord_secret_id: str = "leaderboard-secret"
    dynamodb_table_name: str = ""
    dynamodb_table_name_parameter: str = "/leaderboard-ddb/table-name"
    aws_region: str = "us-east-1"
    session_duration_seconds: int = Field(default=604800, gt=0)

    @model_validator(mode="after")
    def validate_urls(self) -> Self:
        frontend = self.frontend_url.rstrip("/")
        for value in (frontend, self.discord_redirect_uri):
            if value is None:
                continue
            try:
                url = urlsplit(value)
                _ = url.port  # Validate the port as well as the hostname.
            except ValueError:
                raise ValueError("Invalid configuration URL") from None
            if (
                url.scheme not in {"http", "https"}
                or not url.hostname
                or url.username is not None
                or url.password is not None
                or url.query
                or url.fragment
                or any(char.isspace() for char in value)
            ):
                raise ValueError(
                    "URLs must be HTTP(S), without credentials, query, or fragment"
                )
            if url.scheme == "http" and url.hostname not in {
                "localhost",
                "127.0.0.1",
                "::1",
            }:
                raise ValueError("HTTPS is required except for localhost")
        if urlsplit(frontend).path:
            raise ValueError("FRONTEND_URL must be an origin without a path")
        object.__setattr__(self, "frontend_url", frontend)
        return self

    @property
    def frontend_origin(self) -> str:
        return self.frontend_url

    @property
    def secure_cookies(self) -> bool:
        return self.frontend_url.startswith("https://")

    @property
    def redirect_uri(self) -> str:
        return self.discord_redirect_uri or f"{self.frontend_url}/api/user/callback"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    values = {}
    for field in Settings.model_fields:
        value = os.getenv(field.upper())
        if value is not None:
            values[field] = value

    values["aws_region"] = (
        os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
    )
    return Settings(**values)


def discord_config() -> dict[str, str]:
    settings = get_settings()
    client_id = settings.discord_client_id
    client_secret = settings.discord_client_secret.get_secret_value()
    if (not client_id or not client_secret) and settings.discord_secret_id:
        secret = get_secrets(settings.discord_secret_id, settings.aws_region)
        client_id = client_id or secret.get("DISCORD_CLIENT_ID", "")
        client_secret = client_secret or secret.get("DISCORD_CLIENT_SECRET", "")
    if (
        not isinstance(client_id, str)
        or not isinstance(client_secret, str)
        or not client_id
        or not client_secret
    ):
        raise ValueError("Discord login is not configured")
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": settings.redirect_uri,
    }


def dynamodb_table_name() -> str:
    settings = get_settings()
    if settings.dynamodb_table_name:
        return settings.dynamodb_table_name
    if settings.dynamodb_table_name_parameter:
        name = get_ssm_param_value(
            settings.dynamodb_table_name_parameter, settings.aws_region
        )
        if name:
            return name
    raise ValueError("DynamoDB table name is not configured")
