from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from shared.config.settings import get_settings


@lru_cache
def get_redis_client():
    """Lazy import: redis is only in the 'worker' extra. Reads REDIS_URL from settings
    (add `redis_url: str = "redis://localhost:6379/0"` to Settings if not already present)."""
    import redis

    url = getattr(get_settings(), "redis_url", "redis://localhost:6379/0")
    return redis.Redis.from_url(url, decode_responses=True)


def publish(channel: str, payload: dict[str, Any]) -> None:
    get_redis_client().publish(channel, json.dumps(payload, default=str))
