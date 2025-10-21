import redis
from litestar.channels import ChannelsPlugin
from litestar.channels.backends.redis import RedisChannelsPubSubBackend

from app.core import settings

if settings.PROXY_SOCKS is None:
    redis_async_client = redis.asyncio.Redis(host=settings.REDIS_HOST_NAME, port=6379)
else:
    redis_async_client = redis.asyncio.Redis(host="localhost", port=6379)

channels_plugin = ChannelsPlugin(backend=RedisChannelsPubSubBackend(redis=redis_async_client),
                                 channels=[settings.REDIS_CHANNEL_NAME])
