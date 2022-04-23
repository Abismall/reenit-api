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


@router.get("/")
def get_servers(db: Session = Depends(get_db), location: Optional[str] = ""):
    server_query = db.query(models.Server)
    servers = server_query.filter(
        models.Server.location.contains(location)).all()
    if not servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no servers available")
    return servers


@router.post("/")
def create_server(server: schemas.Server, db: Session = Depends(get_db)):
    new_server = models.Server(**server.dict())
    db.add(new_server)
    db.commit()
    return new_server


@router.put("/")
def update_server(server: schemas.Server, db: Session = Depends(get_db)):
    server_query = db.query(models.Server).filter(
        models.Server.id == server.id)
    if server_query.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"location(s) not available")
    server_query.update(server.dict(), synchronize_session=False)
    db.commit()
    return {"data": server_query.first()}


@router.put("/status{event}")
async def status_update(request: Request, db: Session = Depends(get_db)):
    match_end_events = ["series_cancel"]
    data = await request.json()
    match_id = data["matchid"]
    team1_score = data["params"]["team1_series_score"]
    team2_score = data["params"]["team2_series_score"]
    event = data["params"]["event"]

    if event in match_end_events:
        server_query = db.query(models.Server)
        server = server_query.filter(
            models.Server.id.ilike(match_id)).first()
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="could not match id with a server")
        try:
            with requests.post(f"https://dathost.net/api/0.1/game-servers/{server.server_id}/stop", auth=(settings.dathost_username, settings.dathost_password)) as api_call:
                return api_call
        except requests.exceptions.RequestException as err:
            print(f"Requests error: {err}")
        except requests.exceptions.HTTPError as err:
            print(f"Requests error: {err}")
