from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas import UserCreateDTO, UserRegistrationSchema


#from app.services.auth_service import get_password_hash

async def create_user(user: UserRegistrationSchema, db: AsyncSession) -> User:
    #db_user = User(username=user.username, hashed_password=get_password_hash(user.password))
    print(user)
    db_user = User(username=user.username, hashed_password=user.password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User))
    return list(result.scalars().all())