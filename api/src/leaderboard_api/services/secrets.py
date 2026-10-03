import json
from functools import lru_cache
from time import monotonic

import boto3
from botocore.exceptions import BotoCoreError, ClientError


@lru_cache(maxsize=16)
def _read_secret(secret_id: str, region: str, window: int) -> dict:
    try:
        response = boto3.client("secretsmanager", region_name=region).get_secret_value(
            SecretId=secret_id
        )
        value = json.loads(response["SecretString"])
        if not isinstance(value, dict):
            raise ValueError("Expected a JSON object")
        return value
    except (BotoCoreError, ClientError, KeyError, ValueError):
        raise ValueError(
            "Unable to load Discord configuration from Secrets Manager"
        ) from None


def get_secrets(secret_id: str, region: str) -> dict:
    return _read_secret(secret_id, region, int(monotonic() // 300)).copy()
