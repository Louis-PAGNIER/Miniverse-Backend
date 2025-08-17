import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.db import Base, engine
from app.api.v1 import users, auth, miniverses
from app.core.docker_status import refresh_docker_status

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(refresh_docker_status())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Miniverse", swagger_ui_parameters={'persistAuthorization': True}, lifespan=lifespan)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(miniverses.router, prefix="/api/v1/miniverses", tags=["Miniverses"])