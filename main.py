from fastapi import FastAPI
from app.routers import user, server, auth, scrim, dathost
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.config import settings
Base.metadata.create_all(bind=engine)
app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(user.router)
app.include_router(server.router)
app.include_router(auth.router)
app.include_router(scrim.router)
app.include_router(dathost.router)


@app.get("/")
def root():
    return {"message": "Hello, world!"}
