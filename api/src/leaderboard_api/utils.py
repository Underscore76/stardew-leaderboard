from datetime import datetime, timezone, timedelta


def current_timestamp() -> int:
    return int(datetime.now(timezone.utc).timestamp())
