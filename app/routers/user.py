from .. import schemas, utils, models, oauth2
from fastapi import FastAPI, HTTPException, Response, status, Depends, APIRouter
from sqlalchemy import exc
from sqlalchemy.orm import Session
from .. database import get_db
from typing import List, Optional
router = APIRouter(
    prefix="/users",
    tags=['Users']
)


@router.post("/", status_code=status.HTTP_201_CREATED, )
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
        return {"data": new_user.username}
    except exc.IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="username or steamid already taken")
    except exc.SQLAlchemyError as e:
        error = type(e)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"{error}")


@router.put("/{username}")
def update_user(user: schemas.UpdateUser, db: Session = Depends(get_db), active_user: int = Depends(oauth2.get_current_user)):
    user_query = db.query(models.User).filter(models.User.id == active_user.id)
    current_user = user_query.first()
    if current_user.id != active_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized")
    if current_user == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"user {username} does not exist")
    if user.password is not None:
        user.password = utils.hash(user.password)
    updated_user = {k: v for k, v in user.dict().items() if v is not None}
    user_query.update(updated_user, synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_200_OK)


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(username: str, db: Session = Depends(get_db), active_user: int = Depends(oauth2.get_current_user)):
    user_query = db.query(models.User).filter(models.User.username == username)
    current_user = user_query.first()
    if current_user.id != active_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized")
    if current_user == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"user {username} does not exist")

    user_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/", response_model=list[schemas.UserOut])
def get_user(db: Session = Depends(get_db), search: Optional[str] = ""):
    user = db.query(models.User).filter(
        models.User.username.contains(search)).all()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"user {search} does not exist")
    return user
