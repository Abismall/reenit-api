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


@router.get("/scrims/", status_code=status.HTTP_200_OK)
def get_all_scrims(db: Session = Depends(get_db)):
    scrim_query = db.query(models.Scrim, func.count(models.Active.title).label("players")).join(
        models.Active, models.Active.title == models.Scrim.title, isouter=True).group_by(models.Scrim.id)

    if not scrim_query.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no lobbies")
    return scrim_query.all()


@router.get("/scrim/", status_code=status.HTTP_200_OK)
def get_single_scrim(scrim: schemas.Scrim, db: Session = Depends(get_db)):
    if scrim.title is None and scrim.server_id is None:
        scrim_query = db.query(models.Scrim).filter(
            models.Scrim.id == scrim.id)
    if scrim.id is None and scrim.server_id is None:
        scrim_query = db.query(models.Scrim).filter(
            models.Scrim.title == scrim.title)
    if scrim.id is None and scrim.title is None:
        scrim_query = db.query(models.Scrim).filter(
            models.Scrim.server_id == scrim.server_id)
    if not scrim_query.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no lobbies")
    players_query = db.query(models.Active).filter(
        models.Active.scrim_id == scrim_query.first().id)
    return {"lobby": scrim_query.first(), "players": players_query.all()}


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
    except exc.IntegrityError as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="1. lobby id/title already exists\n 2. you have already created a lobby")
    except exc.SQLAlchemyError as e:
        print(e)
        error = type(e)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"{error}")

    try:
        new_active = models.Active(
            title=new_scrim.title, user_id=current_user.id, scrim_id=new_scrim.id, username=current_user.username, steam64=current_user.steam64)
        db.add(new_active)
        db.commit()
        print(new_scrim)
        return {"detail": (new_scrim.title, current_user.username)}
    except exc.IntegrityError as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="1. you can only create one lobby\n 2. you cannot create a lobby if you are already in one")
    except exc.SQLAlchemyError as e:
        print(e)
        error = type(e)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"{error}")


@ router.post("/scrim/", status_code=status.HTTP_200_OK)
def join_scrim(scrim: schemas.Scrim, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    print(scrim)
    if current_user == None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="not logged in")
    active_query = db.query(models.Active).filter(
        models.Active.title == scrim.title)
    lobby_query = db.query(models.Scrim).filter(
        models.Scrim.title.contains(scrim.title))
    current_lobby = lobby_query.first()
    if not current_lobby:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="no such lobby")
    if len(active_query.all()) >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="lobby is full")
    if active_query.filter(models.Active.user_id == current_user.id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="user already in a lobby")
    user = db.query(models.User).filter(
        models.User.id == current_user.id).first()
    new_active = models.Active(
        title=lobby, user_id=current_user.id, username=user.username, scrim_id=current_lobby.id, steam64=user.steam64)
    db.add(new_active)
    db.commit()
    db.refresh(new_active)
    return new_active


@router.delete("/", status_code=status.HTTP_200_OK)
def leave_scrim(user: schemas.UserQuery, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if current_user == None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="login failure")
    lobby_query = db.query(models.Active).filter(
        models.Active.user_id == current_user.id and models.Active.username == user.username)
    found_in = lobby_query.first()
    if not found_in:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="not in a lobby")
    owner_query = db.query(models.Scrim).filter(
        models.Scrim.owner_id == current_user.id)
    if owner_query.first():
        owner_query.delete(synchronize_session=False)
        db.commit()
    lobby_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_200_OK)


@router.put("/", status_code=status.HTTP_200_OK)
def update_lobby(scrim: schemas.Scrim, db: Session = Depends(get_db)):
    new_scrim = {k: v for k, v in scrim.dict().items()
                 if k == "team_one" or k == "team_two" or v != None}
    lobby = db.query(models.Scrim).filter(
        models.Scrim.title == scrim.title)
    if not lobby.first():
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    lobby.update(new_scrim, synchronize_session=False)
    db.commit()
    return lobby.first()
