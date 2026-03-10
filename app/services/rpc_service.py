import asyncio
from typing import Callable, Coroutine, Any

import aiohttp
import websockets
from aiohttp_socks import ProxyConnector
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
        if value is not None:
            self._connected.set()

    async def call_rpc(self, method_name: str, *args, **kwargs):
        method = getattr(await self.server, method_name)
        return await method(*args, **kwargs)

    async def add_handler(self, method_name: str, callback: Callable[[dict], None] | Coroutine[Any, Any, None]):
        return setattr(await self.server, method_name, callback)

    async def connect_loop(self):
        """Boucle de connexion avec reconnexion automatique basique."""
        while True:
            connector = None
            if settings.PROXY_SOCKS:
                connector = ProxyConnector.from_url(settings.PROXY_SOCKS)
            async with aiohttp.ClientSession(connector=connector) as session:
                server = Server(
                    url=self.url,
                    headers=self.headers,
                    session=session,
                )

                try:
                    await server.ws_connect()
                    self._server = server
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("Connexion fermée par le serveur.")
                except Exception as e:
                    logger.error(f"Erreur de connexion : {e}")
                finally:
                    await server.close()

            # Si on sort du bloc 'async with', on est déconnecté
            self._server = None
            logger.info("Tentative de reconnexion dans 3 secondes...")
            await asyncio.sleep(3)  # Délai avant de tenter de se reconnecter
