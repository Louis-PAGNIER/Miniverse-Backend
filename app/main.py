from fastapi import FastAPI
from app.db import Base, engine
from app.api.v1 import users, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Miniverse", swagger_ui_parameters={'persistAuthorization': True})

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])