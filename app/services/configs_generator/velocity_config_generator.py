from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Proxy, Miniverse


async def generate_velocity_config(proxy: Proxy, db: AsyncSession):
    config = {
        "config-version": "2.7",
        "bind": "0.0.0.0:25565",
        "motd": "<#09add3>A Miniverse Server",
        "show-max-players": 404,
        "online-mode": False,
        "force-key-authentication": False,
        "prevent-client-proxy-connections": False,
        "player-info-forwarding-mode": "none",
        "forwarding-secret-file": "forwarding.secret",
        "announce-forge": False,
        "kick-existing-players": False,
        "ping-passthrough": "disabled",
        "enable-player-address-logging": True,

        "servers": {
            #"lobby": "<container-id>:25565",
            "try": [
                # "lobby",
                # "factions"
            ],
        },

        "forced-hosts": {
            #"localhost": ["lobby"],
        },

        "advanced": {
            "compression-threshold": 256,
            "compression-level": -1,
            "login-ratelimit": 0,
            "connection-timeout": 5000,
            "read-timeout": 30000,
            "haproxy-protocol": False,
            "tcp-fast-open": False,
            "bungee-plugin-message-channel": True,
            "show-ping-requests": False,
            "failover-on-unexpected-server-disconnect": True,
            "announce-proxy-commands": True,
            "log-command-executions": False,
            "log-player-connections": True,
            "accepts-transfers": True,
        },

        "query": {
            "enabled": False,
            "port": 25565,
            "map": "Velocity",
            "show-plugins": False
        }
    }

    await db.refresh(proxy, attribute_names=["miniverses"])

    mv: Miniverse
    for mv in proxy.miniverses:
        config["servers"][mv.id] = f"miniverse-{mv.id}:25565"
        config["servers"]["try"].append(mv.id)
        config["forced-hosts"][f"{mv.subdomain}.miniverse.fr"] = [mv.id]

    return config