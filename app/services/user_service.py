from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import logger
from app.models.user import User
from app.schemas import UserCreate
from app.services.auth_service import get_password_hash

async def create_user(user: UserCreate, db: AsyncSession) -> User:
    logger.info(f"Creating user {user.username} with role {user.role}")
    db_user = User(username=user.username, hashed_password=get_password_hash(user.password), role=user.role)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User))
    return list(result.scalars().all())


async def get_user(user_id: str, db: AsyncSession) -> User | None:
    return await db.get(User, user_id)


async def get_user_by_username(username: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()