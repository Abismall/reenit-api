from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from app import database, schemas, models, utils, oauth2

router = APIRouter(tags=['Authentication'])


@router.post("/login", response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(
        models.User.username == user_credentials.username).first()

    if not user:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            detail="invalid credentials")
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            detail="invalid credentials")
    access_token = oauth2.create_access_token(
        data={"user_id": user.id, "username": user.username, "steam64": user.steam64})
    data = {"token": access_token, "token_type": "bearer"}
    print(data)
    return data
