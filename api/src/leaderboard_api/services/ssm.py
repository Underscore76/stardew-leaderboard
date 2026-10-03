from functools import lru_cache
from time import monotonic

import boto3


@lru_cache(maxsize=16)
def _read_parameter(name: str, region: str, window: int) -> str | None:
    response = boto3.client("ssm", region_name=region).get_parameter(Name=name)
    return response.get("Parameter", {}).get("Value")


def get_ssm_param_value(name: str, region: str) -> str | None:
    return _read_parameter(name, region, int(monotonic() // 300))
