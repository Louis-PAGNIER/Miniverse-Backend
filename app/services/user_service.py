from sqlalchemy import select, delete, func
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


async def get_user(user_id: str, db: AsyncSession) -> User | None:
    return await db.get(User, user_id)


async def get_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).where(User.is_active == True))
    return list(result.scalars().all())


async def count_admins(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(User.id)).where(User.role == Role.ADMIN))
    return result.scalar()


async def get_user_by_username(username: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()


async def delete_user(user_id: str, db: AsyncSession) -> None:
    logger.info(f"Deleting user {user_id}")
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()


async def set_user_role(user_id: str, role: Role, db: AsyncSession) -> None:
    logger.info(f"Setting role {role}")
    user = await get_user(user_id, db)
    user.role = role
    await db.commit()


async def get_inactive_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).where(User.is_active == False))
    return list(result.scalars().all())


async def accept_user_request(user_id: str, db: AsyncSession) -> None:
    user = await get_user(user_id, db)
    user.is_active = True
    await db.commit()


async def reject_user_request(user_id: str, db: AsyncSession) -> None:
    await delete_user(user_id, db)