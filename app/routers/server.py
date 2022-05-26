from app import schemas, models
from fastapi import HTTPException, status, Request, Depends, APIRouter
from sqlalchemy import exc
from sqlalchemy.orm import Session
from app.database import get_db
from typing import Optional
import requests
from .. config import settings
router = APIRouter(
    prefix="/servers",
    tags=['Servers']
)


@router.get("/", status_code=status.HTTP_200_OK)
def get_servers(db: Session = Depends(get_db)):
    server_query = db.query(models.Server)
    servers = server_query.all()
    if not servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no servers available")
    return servers


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_server(server: schemas.Server, db: Session = Depends(get_db)):
    new_server = models.Server(**server.dict())
    db.add(new_server)
    db.commit()
    return new_server


@router.put("/", status_code=status.HTTP_200_OK)
def update_server(server: schemas.Server, db: Session = Depends(get_db)):
    server_query = db.query(models.Server).filter(
        models.Server.id == server.id)
    if server_query.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"location(s) not available")
    server_query.update(server.dict(), synchronize_session=False)
    db.commit()
    return {"data": server_query.first()}


@router.post("/status/event", status_code=status.HTTP_201_CREATED)
async def status_update(request: Request, db: Session = Depends(get_db)):
    match_end_events = ["series_cancel", "series_end", "map_end"]
    data = await request.json()
    match_id = data["matchid"]
    event = data["event"]
    if event in match_end_events:
        scrim_query = db.query(models.Scrim).filter(
            models.Scrim.id == int(match_id)).first()

        try:
            requests.post(f"https://dathost.net/api/0.1/game-servers/{scrim_query.server_id}/stop", auth=(
                settings.dathost_username, settings.dathost_password))
        except requests.exceptions.RequestException as err:
            print(f"Requests error: {err}")
        except requests.exceptions.HTTPError as err:
            print(f"Requests error: {err}")
        finally:
            scrim_query.delete(synchronize_session=False)
        db.commit()
