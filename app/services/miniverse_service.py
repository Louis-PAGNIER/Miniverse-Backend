from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Miniverse


def get_miniverses(db: Session):
    return list(db.scalars(select(Miniverse)).all())