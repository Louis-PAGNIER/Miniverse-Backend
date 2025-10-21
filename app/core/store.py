from litestar.stores.redis import RedisStore

from app.core import settings

if settings.PROXY_SOCKS is None:
    root_store = RedisStore.with_client(url="redis://miniverse-redis:6379")
else:
    root_store = RedisStore.with_client(url="redis://localhost:6379")

# TODO : Why is three 2 redis client ?
# TODO : Can we use app/core/channels.py instead ?
