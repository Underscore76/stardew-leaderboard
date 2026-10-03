from leaderboard_api.models.user import User
from leaderboard_api.services.ddb import get_table


def get_user(user_id: str) -> User | None:
    result = get_table().get_item(
        Key={"pk": "PROFILE", "sk": f"USER#{user_id}"}, ConsistentRead=True
    )
    item = result.get("Item")
    return User.model_validate(item) if item else None


def sync_discord_user(
    user_id: str, *, username: str, avatar: str | None, display_name: str
) -> User:
    result = get_table().update_item(
        Key={"pk": "PROFILE", "sk": f"USER#{user_id}"},
        UpdateExpression=(
            "SET user_id = :id, username = :username, avatar = :avatar, "
            "display_name = if_not_exists(display_name, :display_name)"
        ),
        ExpressionAttributeValues={
            ":id": user_id,
            ":username": username,
            ":avatar": avatar,
            ":display_name": display_name,
        },
        ReturnValues="ALL_NEW",
    )
    return User.model_validate(result["Attributes"])


def update_display_name(user_id: str, display_name: str) -> User:
    result = get_table().update_item(
        Key={"pk": "PROFILE", "sk": f"USER#{user_id}"},
        UpdateExpression="SET display_name = :name",
        ConditionExpression="attribute_exists(pk)",
        ExpressionAttributeValues={":name": display_name},
        ReturnValues="ALL_NEW",
    )
    return User.model_validate(result["Attributes"])
