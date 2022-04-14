from pydantic import BaseModel
from typing import Optional


class RegisterUser(BaseModel):
    steam64: int
    username: str
    password: str


class UpdateUser(BaseModel):
    username: Optional[str]
    password: Optional[str]
    public: Optional[bool]
    steam64: Optional[int]


class Location(BaseModel):
    active: Optional[bool]
    location: Optional[str]
    id: Optional[int]


class UserOut(BaseModel):
    id: Optional[int]
    username: Optional[str]
    steam64: Optional[int]
    public: Optional[bool]

    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    username: str
    password: str


class UserLobby(BaseModel):
    lobby_id: int
    lobby_owner: int


class Token(BaseModel):
    token: str
    token_type: str


class TokenData(BaseModel):
    id: str


class ScrimBase(BaseModel):
    title: str
    public: bool = True
