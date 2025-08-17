from datetime import datetime, timedelta, timezone
from typing import Optional, Annotated

from jose import jwt, JWTError
import bcrypt
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.enums import Role
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user: Optional[User] = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_moderator_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role < Role.MODERATOR:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role < Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

CurrentUser = Annotated[User, Depends(get_current_user)]
ModeratorUser = Annotated[User, Depends(get_moderator_user)]
AdminUser = Annotated[User, Depends(get_admin_user)]