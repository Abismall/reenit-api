from .. import schemas, utils, models, oauth2
from fastapi import HTTPException, Response, status, Depends, APIRouter, Body
from sqlalchemy import exc
from sqlalchemy.orm import Session
from app.database import get_db
from typing import List, Any
import requests
from .. steam.steamidParser import steam64_from_url
router = APIRouter(
    prefix="/users",
    tags=['Users']
)


@router.post("/", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.RegisterUser, db: Session = Depends(get_db)):
    hashed_password = utils.hash(user.password)
    user.password = hashed_password
    new_user = models.User(**user.dict())
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User could not be created")
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except exc.IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="username or steamid already taken")
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")


@router.put("/", response_model=schemas.UserOut, status_code=status.HTTP_200_OK)
def update_user(user: schemas.UpdateUser, db: Session = Depends(get_db), active_user: int = Depends(oauth2.get_current_user)):
    updated_user = {k: v for k, v in user.dict().items() if v is not None}
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if not active_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="not logged in")
    user_query = db.query(models.User).filter(models.User.id == active_user.id)
    current_user = user_query.first()
    if current_user.id != active_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if current_user == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="no user(s)")
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="no user(s)")
    if user.password is not None:
        user.password = utils.hash(user.password)
    user_query.update(updated_user, synchronize_session=False)
    db.commit()
    return


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(db: Session = Depends(get_db), active_user: int = Depends(oauth2.get_current_user)):
    if not active_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="not logged in")
    user_query = db.query(models.User).filter(models.User.id == active_user.id)
    current_user = user_query.first()
    if current_user.id != active_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized")
    if current_user == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="no user(s)")

    user_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/user", response_model=schemas.UserOut, status_code=status.HTTP_200_OK)
def get_user(db: Session = Depends(get_db), active_user: int = Depends(oauth2.get_current_user)):
    if not active_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    user_query = db.query(models.User).filter(
        models.User.id == active_user.id)
    if not user_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"no user(s)")

    return user_query.first()


@ router.get("/users", response_model=List[schemas.UserOut], status_code=status.HTTP_200_OK)
def get_users(db: Session = Depends(get_db)):
    user_query = db.query(models.User)
    if not user_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"no user(s)")
    return user_query.all()


@ router.get("/user/current", status_code=status.HTTP_200_OK)
def get_current_game(db: Session = Depends(get_db), active_user: int = Depends(oauth2.get_current_user)):
    if not active_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    user_query = db.query(models.Active).filter(
        models.Active.id == active_user.id)
    if not user_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"no user(s)")
    lobby_query = db.query(models.Scrim).filter(
        models.Scrim.title == user_query.first().title)
    players_query = db.query(models.Active).filter(
        models.Active.title == user_query.first().title)
    data = {
        "lobby": lobby_query.first(),
        "Players": players_query.all(),
        "team_one": db.query(models.Active).filter(
            models.Active.title == user_query.first().title).filter(models.Active.team == 1).all(),
        "team_two": db.query(models.Active).filter(
            models.Active.title == user_query.first().title).filter(models.Active.team == 2).all(),
    }
    return data


@ router.post("/user/actions/scrim/", status_code=status.HTTP_200_OK)
def switch_team(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    user_query = db.query(models.Active).filter(
        models.Active.id == current_user.id
    )
    if not user_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Could not locate user in active games")
    team_select = {1: {"team": 2}, 2: {"team": 1}}
    if user_query.first().team is None:
        new_team = team_select[1]
    else:
        new_team = team_select[user_query.first().team]
    user_query.update(
        new_team, synchronize_session=False)
    db.commit()
    return user_query.first()


@ router.get("/user/actions/steamprofile", status_code=status.HTTP_200_OK)
async def get_steam_for_user(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    user_query = db.query(models.User).filter(
        models.User.id == current_user.id)
    steam64 = user_query.first().steam64

    data = requests.get(
        f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=7BF81648CA090CDC4D84E509AEA6E46F&steamids={steam64}")
    try:
        data.json()["response"]["players"][0]
        return data.json()["response"]["players"][0]
    except:
        return None


@ router.get("/user/actions/steamprofile/{id}", status_code=status.HTTP_200_OK)
async def get_steam_by_id(id: str, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    data = requests.get(
        f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=7BF81648CA090CDC4D84E509AEA6E46F&steamids={id}")
    try:
        data.json()["response"]["players"][0]
        return data.json()["response"]["players"][0]
    except:
        return None


@ router.post("/user/actions/verify/", status_code=status.HTTP_200_OK)
async def verify_steam(url: dict):
    try:
        steam64 = steam64_from_url(url["url"])
        data = {"steam64": steam64}
        return data
    except:
        return Response(status.HTTP_400_BAD_REQUEST)
