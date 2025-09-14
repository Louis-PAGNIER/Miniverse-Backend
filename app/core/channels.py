import redis

from litestar.channels import ChannelsPlugin
from litestar.channels.backends.redis import RedisChannelsPubSubBackend

redis_async_client = redis.asyncio.Redis(host="miniverse-redis", port=6379)
channels_plugin = ChannelsPlugin(backend=RedisChannelsPubSubBackend(redis=redis_async_client), channels=["miniverse-updates"])