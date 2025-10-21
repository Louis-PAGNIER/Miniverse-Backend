from litestar.stores.redis import RedisStore

from app.core.channels import redis_async_client

root_store = RedisStore(redis=redis_async_client)
