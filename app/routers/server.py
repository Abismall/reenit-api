from .. import schemas, models
from fastapi import HTTPException, status, Depends, APIRouter
from sqlalchemy import exc
from sqlalchemy.orm import Session
from .. database import get_db
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


@router.put("/{id}")
def update_server(id: int, location: schemas.Location, db: Session = Depends(get_db)):
    server_query = db.query(models.Location).filter(models.Location.id == id)
    if server_query.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"location {id} does not exist")
    server_query.update(location.dict(), synchronize_session=False)
    db.commit()
    return {"data": server_query.first()}
