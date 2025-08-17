from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.auth_service import get_password_hash

def create_user(db: Session, user: UserCreate) -> User:
    db_user = User(username=user.username, hashed_password=get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session) -> list[User]:
    return list(db.scalars(select(User)).all())