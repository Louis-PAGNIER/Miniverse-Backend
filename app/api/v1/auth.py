from datetime import timedelta
from typing import Annotated

from litestar import post, Response
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.params import Body
from litestar.security.jwt import OAuth2Login
from sqlalchemy.ext.asyncio import AsyncSession

from app import get_db_session
from app.core import settings
from app.schemas import UserCreate
from app.services.auth_service import verify_password, oauth2_auth
from app.services.user_service import get_user_by_username


@post("/login", dependencies = {"db": Provide(get_db_session)}, tags=["Authentication"])
async def login(data: Annotated[UserCreate, Body(media_type=RequestEncodingType.URL_ENCODED)], db: AsyncSession) -> Response[OAuth2Login]:
    user = await get_user_by_username(data.username, db)
    if not user or not verify_password(data.password, user.hashed_password):
        raise NotFoundException(detail="User not found or password is incorrect")
    return oauth2_auth.login(identifier=str(user.id), token_expiration=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))