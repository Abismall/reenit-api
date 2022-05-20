from re import S
from .. import schemas, models, oauth2
from fastapi import HTTPException, status, Depends, APIRouter, Response, Request
from sqlalchemy import exc, func
from sqlalchemy.orm import Session
from .. database import get_db
from .. import schemas
from typing import List
router = APIRouter(
    prefix="/reenit",
    tags=['Reenit']
)


@router.get("/scrims/", status_code=status.HTTP_200_OK)
def get_all_scrims(db: Session = Depends(get_db)):
    scrim_query = db.query(models.Scrim)
    if not scrim_query.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no lobbies")
    return scrim_query.all()


@router.get("/scrim/{title}", status_code=status.HTTP_200_OK)
async def get_single_scrim(title, request: Request, db: Session = Depends(get_db)):
    if title:
        lobby_query = db.query(models.Scrim).filter(
            models.Scrim.title == title)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if not lobby_query.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no lobbies")
    user_query = db.query(models.Active).filter(
        models.Active.title == title)

    data = {
        "lobby": lobby_query.first(),
        "Players": user_query.all(),
        "team_one": db.query(models.Active).filter(
            models.Active.title == user_query.first().title).filter(models.Active.team == 1).all(),
        "team_two": db.query(models.Active).filter(
            models.Active.title == user_query.first().title).filter(models.Active.team == 2).all(),
    }
    return data


@ router.post("/scrims/", status_code=status.HTTP_201_CREATED)
def create_scrim(scrim: schemas.Scrim, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if len(scrim.title) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No title")
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="not logged in")

    db.query(models.Scrim).filter(
        models.Scrim.owner_id == current_user.id).delete()
    db.query(models.Active).filter(
        models.Active.id == current_user.id).delete()

    db.commit()
    new_scrim = models.Scrim(owner_id=current_user.id,
                             title=scrim.title)

    if not new_scrim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="scrim could not be created")

    try:
        db.add(new_scrim)
        db.commit()
    except exc.IntegrityError as e:
        db.rollback()
        new_scrim = models.Scrim(owner_id=current_user.id,
                                 title=scrim.title)
        db.query(models.Scrim).filter(
            models.Scrim.owner_id == current_user.id).delete()
        db.add(new_scrim)
        raise HTTPException(status_code=status.HTTP_205_RESET_CONTENT,
                            detail="lobby id/title already exists")
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{e}")

    new_active = models.Active(
        title=new_scrim.title, id=current_user.id, username=current_user.username, steam64=current_user.steam64, team=1)
    db.add(new_active)
    db.commit()
    return


@ router.post("/scrim/", status_code=status.HTTP_200_OK)
def join_scrim(scrim: schemas.Scrim, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if not current_user:
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
    if active_query.filter(models.Active.id == current_user.id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="user already in a lobby")
    user = db.query(models.User).filter(
        models.User.id == current_user.id).first()
    new_active = models.Active(
        title=scrim.title, id=current_user.id, username=user.username, steam64=user.steam64)
    db.add(new_active)
    db.commit()
    db.refresh(new_active)
    return new_active


@router.delete("/", status_code=status.HTTP_200_OK)
def leave_scrim(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="login failure")
    lobby_query = db.query(models.Active).filter(
        models.Active.id == current_user.id)
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


@router.put("/scrim/update", status_code=status.HTTP_200_OK)
async def update_lobby(scrim: schemas.Scrim, current_user: int = Depends(oauth2.get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        raise Exception(status_code=status.HTTP_403_FORBIDDEN)
    new_scrim = {k: v for k, v in scrim.dict().items()
                 if k == "team_one" or k == "team_two" or v != None}

    players_query = db.query(models.Active).filter(
        models.Active.id == current_user.id)
    if not players_query.first():
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    lobby_query = db.query(models.Scrim).filter(
        models.Scrim.title == players_query.first().title)
    if not lobby_query.first():
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    lobby_query.update(new_scrim, synchronize_session=False)
    db.commit()
    data = {
        "lobby": lobby_query.first(),
        "Players": players_query.all(),
        "team_one": players_query.filter(models.Active.team == 1).all(),
        "team_two": players_query.filter(models.Active.team == 2).all(),
    }
    return data


@router.put("/scrim/update/switch", status_code=status.HTTP_200_OK)
async def move_players(user_id_list: list, current_user: int = Depends(oauth2.get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        raise Exception(status_code=status.HTTP_403_FORBIDDEN)
    team_select = {1: {"team": 2}, 2: {"team": 1}}
    try:
        for user_id in user_id_list:
            user_query = db.query(models.Active).filter(
                models.Active.id == user_id
            )

            if user_query.first().team is None:
                new_team = team_select[1]
            else:
                new_team = team_select[user_query.first().team]
            user_query.update(
                new_team, synchronize_session=False)
            db.commit()
    except:
        pass
