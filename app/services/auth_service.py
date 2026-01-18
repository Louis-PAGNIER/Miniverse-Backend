from typing import Any

from keycloak import KeycloakOpenID
from litestar import Request
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.handlers import BaseRouteHandler
from litestar.security.jwt import Token, JWTCookieAuth

from app import get_db_session
from app.core import settings
from app.models import User
from app.services.user_service import create_user


def get_keycloak_openid():
    return KeycloakOpenID(server_url=settings.KEYCLOAK_ISSUER,
                          client_id=settings.KEYCLOAK_CLIENT_ID,
                          realm_name=settings.KEYCLOAK_REALM)


def get_keycloak_public_key():
    """
    Retrieves the public key from the Keycloak OpenID provider.

    Returns:
        str: The public key in PEM format.
    """
    keycloak_openid = get_keycloak_openid()
    return "-----BEGIN PUBLIC KEY-----\n" + keycloak_openid.public_key() + "\n-----END PUBLIC KEY-----\n"


async def retrieve_user_handler(token: Token, _: ASGIConnection[Any, Any, Any, Any]) -> User | None:
    async for session in get_db_session():
        user = await session.get(User, token.sub)
        if user is None:
            user = await create_user(token.sub, token.extras["preferred_username"], session)

        return user if user.is_active else None  # TODO Return special error so front display some "need activation" or "token expired"
    return None


async def get_current_user(request: Request[User, Token, Any]) -> User:
    return request.user


def admin_user_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    if not connection.user.is_admin:
        raise NotAuthorizedException()


def moderator_user_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    if not connection.user.is_moderator:
        raise NotAuthorizedException()


jwtAuth = JWTCookieAuth[User](
    retrieve_user_handler=retrieve_user_handler,
    token_secret=get_keycloak_public_key(),
    algorithm="RS256",
    exclude=["/docs"]
)
