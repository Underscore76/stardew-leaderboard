from boto3.dynamodb.conditions import Key

from leaderboard_api.models.session import Session
from leaderboard_api.services.ddb import get_table


def get_session(session_id: str) -> Session | None:
    response = get_table().query(
        KeyConditionExpression=Key("pk").eq(f"SESSION#{session_id}"),
        ConsistentRead=True,
        Limit=2,
    )
    items = response.get("Items", [])
    if len(items) > 1 or response.get("LastEvaluatedKey"):
        raise ValueError("A session ID must identify exactly one session")
    return Session.model_validate(items[0]) if items else None


def create_session(session: Session) -> Session:
    get_table().put_item(
        Item={"pk": session.pk, "sk": session.sk, **session.model_dump()},
        ConditionExpression="attribute_not_exists(pk)",
    )
    return session


def delete_session(session: Session) -> None:
    get_table().delete_item(Key={"pk": session.pk, "sk": session.sk})
