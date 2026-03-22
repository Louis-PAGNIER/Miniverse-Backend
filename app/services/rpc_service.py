import asyncio
from typing import Callable

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
        self._server: Server | None = None
        self._connected = asyncio.Event()

    @property
    async def server(self) -> Server:
        await self._connected.wait()
        assert self._server is not None
        return self._server

    @server.setter
    def server(self, value):
        self._server = value
        if value is None:
            self._connected.clear()
        else:
            self._connected.set()

    async def async_call_rpc(self, method_name: str, *args, **kwargs):
        method = getattr(await self.server, method_name)
        return await method(*args, **kwargs)

    async def async_add_handler(self, method_name: str, callback: Callable):
        return setattr(await self.server, method_name, callback)

    async def async_connect_loop(self):
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

                    while server.connected:
                        await asyncio.sleep(1)

                except websockets.exceptions.ConnectionClosed:
                    logger.warning("Connexion fermée par le serveur.")
                except ProxyError as e:
                    if e.args[0] == "Host unreachable":
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
