from typing import Any

import bcrypt
from litestar import Request
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException, InternalServerException
from litestar.handlers import BaseRouteHandler
from litestar.security.jwt import Token, OAuth2PasswordBearerAuth

from app import get_db_session
from app.core import settings
from app.models import User


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

async def retrieve_user_handler(token: Token, connection: ASGIConnection[Any, Any, Any, Any]) -> User | None:
    async for session in get_db_session():
        return await session.get(User, token.sub)
    return None

async def get_current_user(request: Request[User, Token, Any]) -> User:
    return request.user

def admin_user_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    if not connection.user.is_admin:
        raise NotAuthorizedException()

def moderator_user_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    if not connection.user.is_moderator:
        raise NotAuthorizedException()

oauth2_auth = OAuth2PasswordBearerAuth[User](
    retrieve_user_handler=retrieve_user_handler,
    token_secret=settings.JWT_SECRET,
    token_url="/login",
    exclude=["/login", "/docs"],
)

