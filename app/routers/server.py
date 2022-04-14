from app import schemas, models
from fastapi import HTTPException, status, Depends, APIRouter
from sqlalchemy import exc
from sqlalchemy.orm import Session
from app.database import get_db
from typing import Optional
router = APIRouter(
    prefix="/servers",
    tags=['Servers']
)


@router.get("/")
def get_locations(db: Session = Depends(get_db), location: Optional[str] = ""):
    locations_query = db.query(models.Location)
    locations = locations_query.filter(
        models.Location.location.contains(location)).all()
    if not locations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no location available")
    return locations


@router.post("/")
def update_server(server: schemas.Location, db: Session = Depends(get_db)):
    new_server = models.Location(**server.dict())
    db.add(new_server)
    db.commit()
    return new_server


@router.put("/")
def update_server(location: schemas.Location, db: Session = Depends(get_db)):
    server_query = db.query(models.Location).filter(
        models.Location.id == location.id)
    if server_query.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"location(s) not available")
    server_query.update(location.dict(), synchronize_session=False)
    db.commit()
    return {"data": server_query.first()}
