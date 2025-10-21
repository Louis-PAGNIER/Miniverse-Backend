import redis
from litestar.channels import ChannelsPlugin
from litestar.channels.backends.redis import RedisChannelsPubSubBackend

from app.core import settings

if settings.HOST_MODE == "docker":
    redis_async_client = redis.asyncio.Redis(host=settings.REDIS_NETWORK_NAME, port=6379)
elif settings.HOST_MODE == "host":
    redis_async_client = redis.asyncio.Redis(host="localhost", port=6379)
else:
    raise ValueError("Host mode must be 'docker' or 'host'")

channels_plugin = ChannelsPlugin(backend=RedisChannelsPubSubBackend(redis=redis_async_client),
                                 channels=[settings.REDIS_CHANNEL_NAME])
