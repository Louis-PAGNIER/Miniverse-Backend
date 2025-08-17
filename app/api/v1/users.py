from fastapi import APIRouter
from app import Db, CurrentUser
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import create_user, get_users

router = APIRouter()

@router.get("/", response_model=list[UserRead])
def list_users(db: Db, current_user: CurrentUser):
    return get_users(db)

@router.post("/", response_model=UserRead)
def register_user(user: UserCreate, db: Db):
    return create_user(db, user)