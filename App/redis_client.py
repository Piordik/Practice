from os import getenv
from redis.asyncio import Redis
from dotenv import load_dotenv

load_dotenv()

redis = Redis(
    host=getenv("REDIS_HOST", "localhost"),
    port=int(getenv("REDIS_PORT", 6379)),
    password=getenv("REDIS_PASSWORD") or None,
    decode_responses=True
)
