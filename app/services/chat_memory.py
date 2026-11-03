import json

from redis import Redis

from app.core.config import settings


redis_client = Redis.from_url(
    settings.redis_url,
    decode_responses=True
)

CHAT_MEMORY_TTL = 86400


def get_chat_history(session_id: str) -> list[dict]:
    """Retrieve previous messages for a conversation."""

    key = f"chat:{session_id}"
    messages = redis_client.lrange(key, 0, -1)

    return [json.loads(message) for message in messages]


def save_chat_message(
    session_id: str,
    role: str,
    content: str
) -> None:
    """Save one message to Redis."""

    key = f"chat:{session_id}"

    message = {
        "role": role,
        "content": content
    }

    redis_client.rpush(key, json.dumps(message))
    redis_client.expire(key, CHAT_MEMORY_TTL)