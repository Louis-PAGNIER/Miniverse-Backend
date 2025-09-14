from litestar.stores.redis import RedisStore

root_store = RedisStore.with_client(url="redis://miniverse-redis:6379")