from .. import schemas, models, oauth2
from fastapi import HTTPException, status, Depends, APIRouter, Response
from sqlalchemy import exc, func
from sqlalchemy.orm import Session
from .. database import get_db
from .. import schemas

router = APIRouter(
    prefix="/reenit",
    tags=['Reenit']
)


@router.get("/scrims/")
def get_all_scrims(db: Session = Depends(get_db)):
    scrim_query = db.query(models.Scrim, func.count(models.Active.title).label("players")).join(
        models.Active, models.Active.title == models.Scrim.title, isouter=True).group_by(models.Scrim.id)

    if not scrim_query.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no lobbies")
    return scrim_query.all()


@router.get("/scrim/")
def get_single_scrim(scrim: schemas.Scrim, db: Session = Depends(get_db)):
    if scrim.title == None:
        scrim_query = db.query(models.Scrim).filter(
            models.Scrim.id == scrim.id)
    else:
        scrim_query = db.query(models.Scrim).filter(
            models.Scrim.title == scrim.title)
    players_query = db.query(models.Active).filter(
        models.Active.title.contains(scrim.title))
    if not scrim_query.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no lobbies")
    return {"lobby": scrim_query.all(), "players": players_query.all()}


@ router.post("/scrims/", status_code=status.HTTP_201_CREATED)
def create_scrim(scrim: schemas.Scrim, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if len(scrim.title) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No title")
    if current_user == None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="not logged in")
    new_scrim = models.Scrim(owner_id=current_user.id,
                             title=scrim.title)

    if not new_scrim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="scrim could not be created")

    try:
        db.add(new_scrim)
        db.commit()
        db.refresh(new_scrim)
        new_active = models.Active(
            title=new_scrim.title, user_id=current_user.id, username=current_user.username, steam64=current_user.steam64, scrim_id=new_scrim.id)
        db.add(new_active)
        db.commit()
        return new_scrim
    except exc.IntegrityError as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="You can only create one lobby")
    except exc.SQLAlchemyError as e:
        print(e)
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
    current_lobby = lobby_query.first()
    if not current_lobby:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="no such lobby")
    if len(lobby_query.all()) >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="lobby is full")
    if active_query.filter(models.Active.user_id == current_user.id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="user already in a lobby")
    user = db.query(models.User).filter(
        models.User.id == current_user.id).first()
    new_active = models.Active(
        title=lobby, user_id=current_user.id, username=user.username, scrim_id=current_lobby.id)
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
    return Response(status_code=status.HTTP_200_OK)


@router.put("/", status_code=status.HTTP_200_OK)
def swap_teams(scrim: schemas.Scrim, db: Session = Depends(get_db)):
    new_scrim = {k: v for k, v in scrim.dict().items()
                 if k == "team_one" or k == "team_two"}
    lobby = db.query(models.Scrim).filter(
        models.Scrim.title == scrim.title)
    lobby.update(new_scrim, synchronize_session=False)
    db.commit()
    return lobby.first()
