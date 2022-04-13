from .. import schemas, models, oauth2
from fastapi import FastAPI, HTTPException, status, Depends, APIRouter, Response
from sqlalchemy import exc, func
from sqlalchemy.orm import Session
from .. database import get_db
from typing import Optional
router = APIRouter(
    prefix="/reenit",
    tags=['Reenit']
)


@router.get("/")
def get_scrims(db: Session = Depends(get_db), lobby: Optional[str] = ""):
    scrim_query = db.query(models.Scrim, func.count(models.Active.title).label("players")).join(
        models.Active, models.Active.title == models.Scrim.title, isouter=True).group_by(models.Scrim.id).filter(models.Scrim.title.contains(lobby)).all()
    if not scrim_query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no lobbies")
    return scrim_query


@ router.post("/scrims/{title}", status_code=status.HTTP_201_CREATED)
def create_scrim(title: str, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if current_user == None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="not logged in")
    new_scrim = models.Scrim(owner_id=current_user.id, title=title)
    if not new_scrim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="scrim could not be created")
    try:
        new_active = models.Active(
            title=new_scrim.title, user_id=current_user.id)
        db.add(new_scrim)
        db.commit()
        db.add(new_active)
        db.commit()
        db.refresh(new_scrim)
        return {"data": new_scrim}
    except exc.IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="You can only create one lobby")
    except exc.SQLAlchemyError as e:
        error = type(e)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"{error}")


@ router.post("/scrim/{lobby}", status_code=status.HTTP_200_OK)
def join_scrim(lobby: str, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if current_user == None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="not logged in")
    active_query = db.query(models.Active).filter(
        models.Active.title.contains(lobby))
    lobby_query = db.query(models.Scrim).filter(
        models.Scrim.title == lobby)
    if not lobby_query.first() or len(lobby_query.all()) >= 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="no such lobby or lobby is full")
    if active_query.filter(models.Active.user_id == current_user.id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="user already in a lobby")
    new_active = models.Active(title=lobby, user_id=current_user.id)
    db.add(new_active)
    db.commit()
    db.refresh(new_active)
    return new_active


@router.delete("/", status_code=status.HTTP_200_OK)
def leave_scrim(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if current_user == None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="not logged in")
    lobby_query = db.query(models.Active).filter(
        models.Active.user_id == current_user.id)
    found_in = lobby_query.first()
    if not found_in:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="not in a lobby")
    lobby_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
