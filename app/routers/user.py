from .. import schemas, utils, models, oauth2
from fastapi import FastAPI, HTTPException, Response, status, Depends, APIRouter
from sqlalchemy import exc
from sqlalchemy.orm import Session
from app.database import get_db
from typing import List, Optional
import json
router = APIRouter(
    prefix="/users",
    tags=['Users']
)


@router.post("/", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED, )
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
        print(e)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="username or steamid already taken")
    except exc.SQLAlchemyError as e:
        print(e)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")


@router.put("/", response_model=schemas.UserOut, status_code=status.HTTP_200_OK)
def update_user(user: schemas.UpdateUser, db: Session = Depends(get_db), active_user: int = Depends(oauth2.get_current_user)):
    updated_user = {k: v for k, v in user.dict().items() if v is not None}
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if active_user == None:
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
    if active_user == None:
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
def get_user(user: schemas.UserQuery, db: Session = Depends(get_db)):
    print(user.username)
    user_query = db.query(models.User).filter(
        models.User.username == user.username)
    if not user_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"no user(s)")
    return user_query.first()


@router.get("/users", response_model=List[schemas.UserOut], status_code=status.HTTP_200_OK)
def get_users(db: Session = Depends(get_db)):
    user_query = db.query(models.User)
    if not user_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"no user(s)")
    return user_query.all()
