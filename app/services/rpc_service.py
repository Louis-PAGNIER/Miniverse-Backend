import asyncio
from typing import Callable, Coroutine, Any

import aiohttp
import websockets
from aiohttp_socks import ProxyConnector, ProxyError
from jsonrpc_websocket import Server

from app import logger
from app.core import settings


class RpcService:
    def __init__(self, url: str, secret: str):
        self.url = url
        self.headers = {"Authorization": f"Bearer {secret}"}
        self.server: Server | None = None

    async def async_call_rpc(self, method_name: str, *args, **kwargs):
        if self.server is None:
            return None
        method = getattr(self.server, method_name)
        return await method(*args, **kwargs)

    def async_add_handler(self, method_name: str, callback: Callable):
        return setattr(self.server, method_name, callback)

    async def async_connect_loop(self, on_connect: Callable[[], Coroutine[Any, Any, None]]):
        """Boucle de connexion avec reconnexion automatique basique."""
        while True:
            connector = None
            if settings.PROXY_SOCKS:
                proxy_url = settings.PROXY_SOCKS.replace("socks5h://", "socks5://")
                connector = ProxyConnector.from_url(proxy_url)
            async with aiohttp.ClientSession(connector=connector) as session:
                server = Server(
                    url=self.url,
                    headers=self.headers,
                    session=session,
                )

                try:
                    await server.ws_connect()
                    self.server = server

                    await on_connect()
                    while server.connected:
                        await asyncio.sleep(1)

                except websockets.exceptions.ConnectionClosed:
                    logger.warning("Connexion fermée par le serveur.")
                except ProxyError as e:
                    if e.args[0] in ["Host unreachable", "Connection refused by destination host"]:
                        logger.debug(e)
                    else:
                        logger.error(e)
                except ConnectionRefusedError as e:
                    logger.debug(e)
                except Exception as e:
                    logger.error(f"Erreur de connexion : {e}")
                finally:
                    await server.close()
                    self.server = None

            logger.debug("Tentative de reconnexion dans 3 secondes...")
            await asyncio.sleep(3)  # Délai avant de tenter de se reconnecter
