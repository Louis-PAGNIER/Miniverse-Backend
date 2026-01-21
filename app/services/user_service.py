from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import logger
from app.enums import Role
from app.models.user import User


async def create_user(userid: str, username: str, db: AsyncSession) -> User:
    logger.info(f"Creating user {username}")
    is_users_empty = (await db.execute(select(User.id).limit(1))).first() is None
    if is_users_empty:
        db_user = User(id=userid, is_active=True, username=username, role=Role.ADMIN)
    else:
        db_user = User(id=userid, username=username)
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
