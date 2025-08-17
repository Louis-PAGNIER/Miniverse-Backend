from fastapi import APIRouter
from app import Db, CurrentUser
from app.schemas.miniverse import MiniverseRead
from app.services.miniverse_service import get_miniverses

router = APIRouter()

@router.get("/", response_model=list[MiniverseRead])
def list_miniverses(db: Db, current_user: CurrentUser):
    return get_miniverses(db)
